import os, sys, time, uuid, re
sys.path.insert(0, os.path.dirname(__file__))

from flask import (Flask, render_template, request, redirect,
                   url_for, session, send_file, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import SECRET_KEY, DATASETS_DIR, MODELS_DIR, MAX_DATASET_MB, MAX_MODEL_MB
from database import (
    init_db, create_user, get_user_by_id, get_user_by_username, get_user_by_email,
    create_project, get_all_projects, get_project, delete_project,
    count_outside_submissions, get_project_submissions,
    get_latest_submission_hash, get_next_block_index, save_submission,
    get_submission, get_user_submissions, get_user_projects
)
from hash_utils import hash_file, combined_submission_hash
from evaluator import evaluate_model
from ethereum import anchor_to_ethereum

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024

init_db()

from config import ETHEREUM_ENABLED
print("=" * 40)
print("Ethereum enabled:", ETHEREUM_ENABLED)
print("=" * 40)

# ── helpers ────────────────────────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.before_request
def load_user():
    uid = session.get("user_id")
    g.user = get_user_by_id(uid) if uid else None

@app.context_processor
def inject_user():
    return {"current_user": g.user}

def safe_name(filename):
    name = secure_filename(filename)
    return name if name else "file"

# ── AUTH ───────────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def register():
    if g.user: return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email    = request.form.get("email","").strip()
        password = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        if not all([username, email, password, confirm]):
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            ok, msg = create_user(username, email, generate_password_hash(password))
            if ok:
                user = get_user_by_username(username)
                session["user_id"] = user["id"]
                return redirect(url_for("home"))
            error = msg
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    if g.user: return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        identifier = request.form.get("identifier","").strip()
        password   = request.form.get("password","")
        user = get_user_by_username(identifier) or get_user_by_email(identifier)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("home"))
        error = "Invalid username/email or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))

# ── HOME ───────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    projects = get_all_projects()
    return render_template("home.html", projects=projects)

# ── PROFILE ────────────────────────────────────────────────────────────────────
@app.route("/profile")
@login_required
def profile():
    my_projects    = get_user_projects(g.user["id"])
    my_submissions = get_user_submissions(g.user["id"])
    return render_template("profile.html",
                           my_projects=my_projects,
                           my_submissions=my_submissions)

# ── CREATE PROJECT ─────────────────────────────────────────────────────────────
@app.route("/projects/new", methods=["GET","POST"])
@login_required
def new_project():
    error = None
    if request.method == "POST":
        name        = request.form.get("name","").strip()
        description = request.form.get("description","").strip()
        dataset_file = request.files.get("dataset")
        if not name:
            error = "Project name is required."
        elif not dataset_file or dataset_file.filename == "":
            error = "Please upload a CSV dataset."
        elif not dataset_file.filename.lower().endswith(".csv"):
            error = "Only .csv files are accepted."
        else:
            dataset_file.seek(0, 2)
            size_mb = dataset_file.tell() / (1024*1024)
            dataset_file.seek(0)
            if size_mb > MAX_DATASET_MB:
                error = f"File exceeds {MAX_DATASET_MB}MB limit."
            else:
                fname        = safe_name(dataset_file.filename)
                dataset_path = os.path.join(DATASETS_DIR, f"{uuid.uuid4().hex}_{fname}")
                dataset_file.save(dataset_path)
                ok, msg = create_project(g.user["id"], name, description, dataset_path, fname)
                if ok:
                    return redirect(url_for("home"))
                error = msg
                try: os.remove(dataset_path)
                except: pass
    return render_template("new_project.html", error=error)

# ── PROJECT DETAIL ─────────────────────────────────────────────────────────────
@app.route("/project/<int:pid>")
def project_detail(pid):
    project = get_project(pid)
    if not project: return render_template("404.html"), 404
    submissions = get_project_submissions(pid)
    best = submissions[0] if submissions else None
    is_owner = g.user and g.user["id"] == project["owner_id"]
    return render_template("project_detail.html",
                           project=project, submissions=submissions,
                           best=best, is_owner=is_owner)

# ── DOWNLOAD DATASET ───────────────────────────────────────────────────────────
@app.route("/project/<int:pid>/download")
def download_dataset(pid):
    project = get_project(pid)
    if not project: return "Project not found", 404
    if not os.path.exists(project["dataset_path"]): return "Dataset not found", 404
    return send_file(project["dataset_path"], as_attachment=True,
                     download_name=project["dataset_name"])

# ── DELETE PROJECT ─────────────────────────────────────────────────────────────
@app.route("/project/<int:pid>/delete", methods=["POST"])
@login_required
def delete_project_route(pid):
    project = get_project(pid)
    if not project: return "Not found", 404
    if project["owner_id"] != g.user["id"]: return "Forbidden", 403
    outside = count_outside_submissions(pid, g.user["id"])
    if outside > 0:
        submissions = get_project_submissions(pid)
        best = submissions[0] if submissions else None
        return render_template("project_detail.html",
                               project=project, submissions=submissions,
                               best=best, is_owner=True,
                               delete_error=f"Cannot delete — {outside} other user(s) have submitted models.")
    delete_project(pid)
    return redirect(url_for("home"))

# ── SUBMIT MODEL ───────────────────────────────────────────────────────────────
@app.route("/project/<int:pid>/submit", methods=["GET","POST"])
@login_required
def submit_model(pid):
    project = get_project(pid)
    if not project: return render_template("404.html"), 404
    error = None
    result = None
    if request.method == "POST":
        model_file = request.files.get("model")
        if not model_file or model_file.filename == "":
            error = "Please upload a .pkl model file."
        elif not model_file.filename.lower().endswith(".pkl"):
            error = "Only .pkl files are accepted."
        else:
            model_file.seek(0, 2)
            size_mb = model_file.tell() / (1024*1024)
            model_file.seek(0)
            if size_mb > MAX_MODEL_MB:
                error = f"Model file exceeds {MAX_MODEL_MB}MB limit."
            else:
                fname      = safe_name(model_file.filename)
                proj_dir   = os.path.join(MODELS_DIR, str(pid))
                os.makedirs(proj_dir, exist_ok=True)
                model_path = os.path.join(proj_dir, f"{uuid.uuid4().hex}_{fname}")
                model_file.save(model_path)

                # Evaluate
                eval_result = evaluate_model(model_path, project["dataset_path"])
                if eval_result["status"] == "error":
                    error = f"Evaluation failed: {eval_result['message']}"
                    try: os.remove(model_path)
                    except: pass
                else:
                    accuracy      = eval_result["accuracy"]
                    model_hash    = hash_file(model_path)
                    timestamp     = time.time()
                    previous_hash = get_latest_submission_hash(pid)
                    block_index   = get_next_block_index(pid)
                    c_hash        = combined_submission_hash(
                                        model_hash, accuracy, g.user["username"],
                                        pid, timestamp, previous_hash)
                    eth_tx, eth_url, eth_mode = anchor_to_ethereum(c_hash, pid)
                    save_submission(pid, g.user["id"], fname, model_path, model_hash,
                                    accuracy, c_hash, eth_tx, eth_url, eth_mode,
                                    block_index, previous_hash,timestamp)
                    result = {
                        "accuracy": accuracy,
                        "model_hash": model_hash,
                        "eth_tx_hash": eth_tx,
                        "eth_tx_url": eth_url,
                        "eth_mode": eth_mode,
                        "block_index": block_index,
                        "method": eval_result.get("method","subprocess"),
                    }
    return render_template("submit.html", project=project, error=error, result=result)

# ── CHAIN VIEW ─────────────────────────────────────────────────────────────────
@app.route("/project/<int:pid>/chain")
def chain_view(pid):
    project = get_project(pid)
    if not project: return render_template("404.html"), 404
    subs = sorted(get_project_submissions(pid), key=lambda x: x["block_index"])
    valid, msg = True, "Chain is valid ✓"
    for sub in subs:
        recheck = combined_submission_hash(sub["model_hash"], sub["verified_accuracy"],
    sub["username"], pid, sub["submitted_at"], sub["previous_hash"])
        if recheck != sub["combined_hash"]:
            valid, msg = False, f"Block #{sub['block_index']} hash mismatch!"; break
    return render_template("chain.html", project=project, submissions=subs,
        chain_valid=valid, chain_msg=msg)

# ── VERIFY ─────────────────────────────────────────────────────────────────────
@app.route("/project/<int:pid>/verify", methods=["GET","POST"])
def verify(pid):
    project = get_project(pid)
    if not project: return render_template("404.html"), 404
    submissions = get_project_submissions(pid)
    result = None
    if request.method == "POST":
        sid = request.form.get("submission_id","")
        if sid:
            sub = get_submission(int(sid))
            if sub and os.path.exists(sub["model_path"]):
                current_hash = hash_file(sub["model_path"])
                if current_hash == sub["model_hash"]:
                    result = {"status": "valid", "sub": sub, "hash": current_hash}
                else:
                    result = {"status": "tampered", "sub": sub,
                              "stored_hash": sub["model_hash"], "current_hash": current_hash}
            else:
                result = {"status": "error", "message": "Submission or model file not found."}
    return render_template("verify.html", project=project,
                           submissions=submissions, result=result)

# ── SUBMISSION DETAIL ──────────────────────────────────────────────────────────
@app.route("/submission/<int:sid>")
def submission_detail(sid):
    sub = get_submission(sid)
    if not sub: return render_template("404.html"), 404
    project = get_project(sub["project_id"])
    return render_template("submission_detail.html", sub=sub, project=project)

@app.route("/project/<int:pid>/leaderboard")
def leaderboard(pid):
    project = get_project(pid)
    if not project:
        return render_template("404.html"), 404
    return render_template("leaderboard.html", project=project,
        submissions=get_project_submissions(pid))


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
