# ChainML — Blockchain ML Model Registry

A Flask web application that combines **Machine Learning** + **Blockchain** + **Cryptographic hashing** to create a tamper-evident model registry.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open browser
# http://localhost:5000
```

## 📁 Project Structure

```
blockchain_ml/
├── app.py              # Flask routes & server
├── blockchain.py       # Block & Blockchain classes
├── model_utils.py      # Train, verify, list models
├── hash_utils.py       # SHA-256 hashing utilities
├── requirements.txt
├── models/             # Saved .pkl model files
└── templates/
    ├── base.html       # Nav, styles, layout
    ├── home.html       # Dashboard + stats
    ├── train.html      # Train & register model
    ├── chain.html      # View all blocks
    ├── verify.html     # Verify model integrity
    └── best.html       # Best accuracy model
```

## ⚙️ How It Works

### Train a Model
1. User enters **username** + **model name**
2. Flask trains a **RandomForest** on the Iris dataset
3. Model is saved as a `.pkl` file
4. **SHA-256 hash** is computed from the file bytes
5. A **new block** is added to the blockchain with metadata

### Verify a Model
1. Load the `.pkl` file
2. Recompute its SHA-256 hash
3. Search the blockchain for a block with that hash
4. **Valid** = hash found in chain | **Tampered** = hash not found

### Blockchain Integrity
- Each block contains: index, timestamp, data, previous_hash, hash
- The chain is validated by recomputing every block's hash
- Any modification to a block will break the chain

## 🔗 API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard |
| `/train` | GET/POST | Train model form |
| `/chain` | GET | View blockchain |
| `/verify` | GET/POST | Verify model |
| `/best` | GET | Best model |
| `/api/chain` | GET | JSON: full chain |
| `/api/stats` | GET | JSON: stats |

## 🛠 Tech Stack
- **Flask** — Web framework
- **scikit-learn** — RandomForest ML model
- **hashlib** — SHA-256 cryptographic hashing
- **pickle** — Model serialization
- **Pure Python** — No external blockchain library
