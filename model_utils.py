import os
import uuid
import pickle
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from hash_utils import hash_model_file

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_model(username: str, model_name: str, project_id: int):
    """Train a RandomForest on Iris, save .pkl under project subfolder."""
    import random

    project_dir = os.path.join(MODELS_DIR, str(project_id))
    os.makedirs(project_dir, exist_ok=True)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    clf = RandomForestClassifier(
        n_estimators=random.randint(50, 150),
        random_state=random.randint(1, 999),
    )
    clf.fit(X_train, y_train)
    accuracy = round(accuracy_score(y_test, clf.predict(X_test)), 4)

    filename = f"{username}_{model_name}_{uuid.uuid4().hex[:6]}.pkl"
    filepath = os.path.join(project_dir, filename)
    with open(filepath, "wb") as f:
        pickle.dump(clf, f)

    model_hash = hash_model_file(filepath)

    return {
        "username": username,
        "model_name": model_name,
        "accuracy": accuracy,
        "model_hash": model_hash,
        "filepath": filepath,
        "filename": filename,
        "project_id": project_id,
    }


def verify_model_file(filepath: str, blockchain):
    """Recompute hash and look up in blockchain."""
    if not os.path.exists(filepath):
        return {"status": "error", "message": "Model file not found on disk."}
    current_hash = hash_model_file(filepath)
    block = blockchain.find_block_by_model(current_hash)
    if block:
        return {
            "status": "valid",
            "block_index": block.index,
            "username": block.data.get("username"),
            "model_name": block.data.get("model_name"),
            "accuracy": block.data.get("accuracy"),
            "hash": current_hash,
        }
    return {
        "status": "tampered",
        "hash": current_hash,
    }


def list_project_models(project_id: int):
    """Return list of {name, path} for all .pkl files under this project."""
    project_dir = os.path.join(MODELS_DIR, str(project_id))
    if not os.path.exists(project_dir):
        return []
    files = [f for f in os.listdir(project_dir) if f.endswith(".pkl")]
    return [{"name": f, "path": os.path.join(project_dir, f)} for f in sorted(files)]
