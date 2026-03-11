import hashlib
import json


def hash_model_file(filepath):
    """Generate SHA-256 hash of a model .pkl file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_dict(data: dict) -> str:
    """Hash a dictionary deterministically."""
    encoded = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()
