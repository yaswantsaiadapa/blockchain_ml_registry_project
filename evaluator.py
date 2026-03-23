import json, os, subprocess, sys, tempfile

# ── evaluation script run inside Docker or subprocess ─────────────────────────
EVAL_SCRIPT = r'''# -*- coding: utf-8 -*-
import pickle, json, sys, warnings, os
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score,
                             mean_squared_error, r2_score)

try:
    task   = sys.argv[1]          # 'classification' or 'regression'
    ds     = sys.argv[2]          # dataset path
    model  = sys.argv[3]          # model path
    use_test = sys.argv[4] if len(sys.argv) > 4 else ""   # optional hidden test path

    df = pd.read_csv(ds)
    target = df.columns[-1]
    X = df.drop(columns=[target]).values
    y = df[target].values

    if use_test and os.path.exists(use_test):
        # use hidden test set — contributor never saw this data
        X_train, y_train = X, y
        df_test = pd.read_csv(use_test)
        X_test  = df_test.drop(columns=[df_test.columns[-1]]).values
        y_test  = df_test[df_test.columns[-1]].values
    else:
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with open(model, "rb") as f:
        m = pickle.load(f)

    preds = m.predict(X_test)

    if task == "regression":
        rmse = round(float(np.sqrt(mean_squared_error(y_test, preds))), 4)
        r2   = round(float(r2_score(y_test, preds)), 4)
        print(json.dumps({"status":"ok","task":"regression",
                          "accuracy": r2,   # use r2 as primary score for ranking
                          "rmse": rmse, "r2_score": r2}))
    else:
        acc  = round(float(accuracy_score(y_test, preds)), 4)
        # f1
        avg  = "binary" if len(set(y_test)) == 2 else "weighted"
        f1   = round(float(f1_score(y_test, preds, average=avg, zero_division=0)), 4)
        # roc-auc — only if model has predict_proba
        roc  = None
        try:
            if hasattr(m, "predict_proba"):
                proba = m.predict_proba(X_test)
                if proba.shape[1] == 2:
                    roc = round(float(roc_auc_score(y_test, proba[:,1])), 4)
                else:
                    roc = round(float(roc_auc_score(y_test, proba, multi_class="ovr", average="weighted")), 4)
        except: pass
        print(json.dumps({"status":"ok","task":"classification",
                          "accuracy": acc, "f1_score": f1, "roc_auc": roc}))
except Exception as e:
    print(json.dumps({"status":"error","message":str(e)}))
'''

def _docker_available():
    try:
        r = subprocess.run(["docker","info"], capture_output=True, timeout=5)
        return r.returncode == 0
    except: return False

def _image_exists():
    try:
        r = subprocess.run(["docker","image","inspect","chainml-evaluator"],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except: return False

def _eval_docker(pkl_path, dataset_path, task, test_path=None):
    pkl_abs     = os.path.abspath(pkl_path).replace("\\","/")
    dataset_abs = os.path.abspath(dataset_path).replace("\\","/")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                     delete=False, dir=os.path.dirname(pkl_abs)) as f:
        f.write(EVAL_SCRIPT)
        script_path = f.name.replace("\\","/")

    cmd = [
        "docker","run","--rm",
        "--network","none",
        "--memory","512m",
        "--cpus","1.0",
        "-v", f"{dataset_abs}:/data/dataset.csv:ro",
        "-v", f"{pkl_abs}:/data/model.pkl:ro",
        "-v", f"{script_path}:/app/eval.py:ro",
    ]
    test_arg = ""
    if test_path and os.path.exists(test_path):
        test_abs = os.path.abspath(test_path).replace("\\","/")
        cmd += ["-v", f"{test_abs}:/data/test.csv:ro"]
        test_arg = "/data/test.csv"

    cmd += ["chainml-evaluator","python","/app/eval.py",
            task, "/data/dataset.csv", "/data/model.pkl"]
    if test_arg:
        cmd.append(test_arg)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"status":"error","message": r.stderr.strip() or "Docker failed."}
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        result = json.loads(lines[-1])
        result["method"] = "docker"
        return result
    except subprocess.TimeoutExpired:
        return {"status":"error","message":"Docker evaluation timed out."}
    except Exception as e:
        return {"status":"error","message":str(e)}
    finally:
        try: os.unlink(script_path)
        except: pass

def _eval_subprocess(pkl_path, dataset_path, task, test_path=None):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(EVAL_SCRIPT)
        script = f.name
    try:
        cmd = [sys.executable, script, task, dataset_path, pkl_path]
        if test_path and os.path.exists(test_path):
            cmd.append(test_path)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"status":"error","message": r.stderr.strip() or "Evaluation failed."}
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        result = json.loads(lines[-1])
        result["method"] = "subprocess"
        return result
    except subprocess.TimeoutExpired:
        return {"status":"error","message":"Evaluation timed out (60s)."}
    except Exception as e:
        return {"status":"error","message":str(e)}
    finally:
        try: os.unlink(script)
        except: pass

def evaluate_model(pkl_path, dataset_path, task="classification", test_path=None):
    if _docker_available() and _image_exists():
        print("[Evaluator] Using Docker sandbox")
        result = _eval_docker(pkl_path, dataset_path, task, test_path)
        if result.get("status") == "ok":
            return result
        print(f"[Evaluator] Docker failed: {result['message']} — falling back to subprocess")
    print("[Evaluator] Using subprocess")
    return _eval_subprocess(pkl_path, dataset_path, task, test_path)
