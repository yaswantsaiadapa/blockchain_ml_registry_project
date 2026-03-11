import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import (
    init_db, create_project, get_all_projects, get_project,
    project_exists, save_block, load_blocks, get_project_model_count
)
from blockchain import Blockchain
from model_utils import train_model, verify_model_file, list_project_models

app = Flask(__name__)
init_db()


def load_chain(project_id: int) -> Blockchain:
    """Load a project's blockchain from SQLite."""
    bc = Blockchain()
    bc.load_from_db(load_blocks(project_id))
    return bc


# ─── HOME ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    projects = get_all_projects()
    for p in projects:
        p["model_count"] = get_project_model_count(p["id"])
    return render_template("home.html", projects=projects)


# ─── PROJECTS ────────────────────────────────────────────────────────────────

@app.route("/projects/new", methods=["GET", "POST"])
def new_project():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        if not name:
            error = "Project name is required."
        elif project_exists(name):
            error = f"A project named '{name}' already exists."
        else:
            pid = create_project(name, desc)
            return redirect(url_for("project_home", project_id=pid))
    return render_template("new_project.html", error=error)


@app.route("/project/<int:project_id>")
def project_home(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    bc = load_chain(project_id)
    best = bc.get_best_model()
    valid, _ = bc.is_chain_valid()
    stats = {
        "blocks": len(bc.chain) - 1,
        "chain_valid": valid,
    }
    return render_template("project_home.html", project=project, stats=stats, best=best)


# ─── TRAIN ───────────────────────────────────────────────────────────────────

@app.route("/project/<int:project_id>/train", methods=["GET", "POST"])
def train(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    result = None
    block = None
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        model_name = request.form.get("model_name", "").strip()
        if not username or not model_name:
            error = "Please fill in all fields."
        else:
            bc = load_chain(project_id)
            result = train_model(username, model_name, project_id)
            block = bc.add_block(result)
            save_block(project_id, block)
    return render_template("train.html", project=project, result=result, block=block, error=error)


# ─── CHAIN ───────────────────────────────────────────────────────────────────

@app.route("/project/<int:project_id>/chain")
def chain(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    bc = load_chain(project_id)
    blocks = bc.to_list()
    valid, msg = bc.is_chain_valid()
    return render_template("chain.html", project=project, blocks=blocks, valid=valid, msg=msg)


# ─── VERIFY ──────────────────────────────────────────────────────────────────

@app.route("/project/<int:project_id>/verify", methods=["GET", "POST"])
def verify(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    models = list_project_models(project_id)
    result = None
    if request.method == "POST":
        filepath = request.form.get("filepath", "").strip()
        if filepath:
            bc = load_chain(project_id)
            result = verify_model_file(filepath, bc)
    return render_template("verify.html", project=project, models=models, result=result)


# ─── BEST ────────────────────────────────────────────────────────────────────

@app.route("/project/<int:project_id>/best")
def best(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    bc = load_chain(project_id)
    block = bc.get_best_model()
    return render_template("best.html", project=project, block=block)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
