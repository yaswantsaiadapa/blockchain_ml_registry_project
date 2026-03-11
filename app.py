import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from blockchain import Blockchain
from model_utils import train_model, verify_model, list_saved_models, MODELS_DIR

app = Flask(__name__)
bc = Blockchain()  # In-memory blockchain (persists for session)


@app.route("/")
def home():
    stats = {
        "blocks": len(bc.chain) - 1,
        "models": len(list_saved_models()),
        "chain_valid": bc.is_chain_valid()[0],
    }
    return render_template("home.html", stats=stats)


@app.route("/train", methods=["GET", "POST"])
def train():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        model_name = request.form.get("model_name", "").strip()
        if not username or not model_name:
            return render_template("train.html", error="Please fill in all fields.")
        result = train_model(username, model_name)
        block = bc.add_block(result)
        return render_template("train.html", result=result, block=block)
    return render_template("train.html")


@app.route("/chain")
def chain():
    blocks = bc.to_list()
    valid, msg = bc.is_chain_valid()
    return render_template("chain.html", blocks=blocks, valid=valid, msg=msg)


@app.route("/verify", methods=["GET", "POST"])
def verify():
    result = None
    models = []
    for fp in list_saved_models():
        models.append({"path": fp, "name": os.path.basename(fp)})

    if request.method == "POST":
        filepath = request.form.get("filepath", "").strip()
        if filepath:
            result = verify_model(filepath, bc)
    return render_template("verify.html", result=result, models=models)


@app.route("/best")
def best():
    block = bc.get_best_model()
    return render_template("best.html", block=block)


# JSON API endpoints
@app.route("/api/chain")
def api_chain():
    return jsonify(bc.to_list())


@app.route("/api/stats")
def api_stats():
    valid, msg = bc.is_chain_valid()
    return jsonify({
        "total_blocks": len(bc.chain),
        "model_blocks": len(bc.chain) - 1,
        "chain_valid": valid,
        "message": msg,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
