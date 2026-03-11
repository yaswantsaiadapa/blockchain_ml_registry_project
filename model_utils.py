import os
import pickle
import uuid
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from hash_utils import hash_model_file

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_model(username: str, model_name: str):
    """Train a RandomForest on Iris dataset, save .pkl, return metadata."""
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=None  # random seed for variation
    )
    clf = RandomForestClassifier(
        n_estimators=__import__("random").randint(50, 150),
        random_state=__import__("random").randint(1, 999),
    )
    clf.fit(X_train, y_train)
    accuracy = round(accuracy_score(y_test, clf.predict(X_test)), 4)

    filename = f"{username}_{model_name}_{uuid.uuid4().hex[:6]}.pkl"
    filepath = os.path.join(MODELS_DIR, filename)
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
    }


def verify_model(filepath: str, blockchain):
    """Load model file, recompute hash, check against blockchain."""
    if not os.path.exists(filepath):
        return {"status": "error", "message": "Model file not found"}

    current_hash = hash_model_file(filepath)
    block = blockchain.find_block_by_model(current_hash)

    if block:
        return {
            "status": "valid",
            "message": "✅ Model is VALID — hash matches blockchain",
            "block_index": block.index,
            "username": block.data.get("username"),
            "model_name": block.data.get("model_name"),
            "accuracy": block.data.get("accuracy"),
            "hash": current_hash,
        }
    else:
        return {
            "status": "tampered",
            "message": "⚠️ Model is TAMPERED — hash not found in blockchain",
            "hash": current_hash,
        }


def list_saved_models():
    files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl")]
    return [os.path.join(MODELS_DIR, f) for f in files]
