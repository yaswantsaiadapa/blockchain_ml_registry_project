import json, os, subprocess, sys, tempfile

EVAL_SCRIPT = '''
import pickle, json, sys
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
try:
    df = pd.read_csv(sys.argv[1])
    target = df.columns[-1]
    X = df.drop(columns=[target]).values
    y = df[target].values
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    with open(sys.argv[2], "rb") as f:
        model = pickle.load(f)
    acc = round(float(accuracy_score(y_test, model.predict(X_test))), 4)
    print(json.dumps({"status": "ok", "accuracy": acc}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
'''

def _docker_available():
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False

def _image_exists():
    try:
        r = subprocess.run(["docker", "image", "inspect", "chainml-evaluator"],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False

def _eval_docker(pkl_path, dataset_path):
    pkl_abs     = os.path.abspath(pkl_path).replace("\\", "/")
    dataset_abs = os.path.abspath(dataset_path).replace("\\", "/")
    
    # Write eval script into a temp file Docker can access
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", 
                                     delete=False, dir=os.path.dirname(pkl_abs)) as f:
        f.write(EVAL_SCRIPT)
        script_path = f.name.replace("\\", "/")

    try:
        r = subprocess.run([
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1.0",
            "-v", f"{dataset_abs}:/data/dataset.csv:ro",
            "-v", f"{pkl_abs}:/data/model.pkl:ro",
            "-v", f"{script_path}:/app/eval.py:ro",
            "chainml-evaluator",
            "python", "/app/eval.py", "/data/dataset.csv", "/data/model.pkl"
        ], capture_output=True, text=True, timeout=120)

        if r.returncode != 0:
            return {"status": "error", "message": r.stderr.strip() or "Docker failed."}
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        result = json.loads(lines[-1])
        result["method"] = "docker"
        return result
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Docker evaluation timed out."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try: os.unlink(script_path)
        except: pass

def _eval_subprocess(pkl_path, dataset_path):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(EVAL_SCRIPT)
        script = f.name
    try:
        r = subprocess.run([sys.executable, script, dataset_path, pkl_path],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"status": "error", "message": r.stderr.strip() or "Evaluation failed."}
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        result = json.loads(lines[-1])
        result["method"] = "subprocess"
        return result
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Evaluation timed out (60s)."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try: os.unlink(script)
        except: pass

def evaluate_model(pkl_path, dataset_path):
    if _docker_available() and _image_exists():
        print("[Evaluator] Using Docker sandbox")
        result = _eval_docker(pkl_path, dataset_path)
        if result.get("status") == "ok":
            return result
        print(f"[Evaluator] Docker failed: {result['message']} — falling back to subprocess")
    print("[Evaluator] Using subprocess")
    return _eval_subprocess(pkl_path, dataset_path)