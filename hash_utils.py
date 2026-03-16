import hashlib, json

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def hash_dict(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def combined_submission_hash(model_hash, accuracy, username, project_id, timestamp, previous_hash):
    return hash_dict({"model_hash": model_hash, "accuracy": str(accuracy),
                      "username": username, "project_id": str(project_id),
                      "timestamp": str(timestamp), "previous_hash": previous_hash})
