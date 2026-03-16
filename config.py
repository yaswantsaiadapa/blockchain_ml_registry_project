import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY    = "chainml-secret-key-change-in-production"
DB_PATH       = os.path.join(BASE_DIR, "chainml.db")
DATASETS_DIR  = os.path.join(BASE_DIR, "datasets")
MODELS_DIR    = os.path.join(BASE_DIR, "models")
UPLOADS_DIR   = os.path.join(BASE_DIR, "uploads")

for d in [DATASETS_DIR, MODELS_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

MAX_DATASET_MB = 50
MAX_MODEL_MB   = 100

# Ethereum Sepolia — fill after SETUP.md steps, leave blank for mock demo mode
INFURA_URL       = os.environ.get("INFURA_URL",       "")
DEPLOYER_ADDRESS = os.environ.get("DEPLOYER_ADDRESS", "")
DEPLOYER_PRIVKEY = os.environ.get("DEPLOYER_PRIVKEY", "")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")
ETHEREUM_ENABLED = all([INFURA_URL, DEPLOYER_ADDRESS, DEPLOYER_PRIVKEY, CONTRACT_ADDRESS])
