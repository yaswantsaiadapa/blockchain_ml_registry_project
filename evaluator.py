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
    preds = model.predict(X_test)
    from sklearn.metrics import accuracy_score
    acc = round(float(accuracy_score(y_test, preds)), 4)
    print(json.dumps({"status": "ok", "accuracy": acc}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
'''

def evaluate_model(pkl_path, dataset_path):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(EVAL_SCRIPT); script = f.name
    try:
        r = subprocess.run([sys.executable, script, dataset_path, pkl_path],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"status": "error", "message": r.stderr.strip() or "Evaluation failed"}
        out = r.stdout.strip().split("\n")[-1]
        result = json.loads(out)
        result["method"] = "subprocess"
        return result
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Evaluation timed out (60s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try: os.unlink(script)
        except: pass
