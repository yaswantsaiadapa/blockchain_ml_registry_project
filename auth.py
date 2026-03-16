import hashlib, hmac, os
from functools import wraps
from flask import session, redirect, url_for, g


def hash_password(password: str) -> str:
    salt   = os.urandom(32).hex()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}${hashed.hex()}"

def check_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(check.hex(), hashed)
    except Exception:
        return False

def login_user(uid: int):
    session["user_id"] = uid
    session.permanent  = True

def logout_user():
    session.pop("user_id", None)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
