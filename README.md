# ChainML

A platform I built where data scientists can collaborate on ML projects. The main idea is simple — when someone submits a trained model, the server evaluates it honestly using Docker, hashes the file, and records the hash permanently on the Ethereum blockchain. Nobody can fake accuracy scores or tamper with old submissions.

I built this because in typical ML competitions or team projects, there's no way to actually verify that someone's claimed accuracy is real, or that they didn't modify their model file after submission. ChainML fixes that.

---

## The core idea

When you submit a model:

1. Server receives the .pkl file
2. Docker container loads it, runs it against the dataset, measures accuracy
3. SHA-256 hash of the file is computed
4. All this gets combined into one hash and sent to my smart contract on Ethereum Sepolia
5. The transaction hash (Etherscan link) gets stored alongside the submission

If anyone touches the model file after submission, the hash changes. The original is on Ethereum forever. Even if my server goes down, the proof exists independently.

---

## How I set it up

**Blockchain side:**
- Created a MetaMask wallet
- Got free Sepolia ETH from Google Cloud faucet
- Created an Infura account for the API endpoint
- Wrote a simple Solidity contract (ModelRegistry.sol) that stores hashes
- Deployed it on Remix IDE connected to MetaMask
- Contract is live at: `0x9057495394eB00c9C26A2EB45893F1fcC8A010b2`

**Backend:**
- Flask handles all the routes and file uploads
- SQLite stores everything needed for the website to work fast
- web3.py signs and sends transactions to Sepolia
- Docker evaluates every model in an isolated container

**Evaluation:**
- Built a Docker image called `chainml-evaluator` with scikit-learn + pandas
- Every uploaded .pkl gets run inside this container
- Container has no internet, 512MB RAM limit, 1 CPU
- The accuracy you see on the leaderboard is what the server measured, not what the user claimed

---

## Running it

Make sure Docker Desktop is open first. Then:

```
python run.py
```

Open `http://127.0.0.1:5000`

The `run.py` file sets the Ethereum credentials before starting Flask. If you don't set them, the app runs in mock mode — everything works the same but Etherscan links are fake. Useful for development.

---

## File structure

```
app.py              — all Flask routes
config.py           — paths and env var reading
database.py         — every SQLite operation
auth.py             — login, password hashing
hash_utils.py       — SHA-256 hashing, block hash computation
evaluator.py        — Docker evaluation with subprocess fallback
ethereum.py         — sends transaction to Sepolia or generates mock
run.py              — sets env vars then starts app

ModelRegistry.sol       — the smart contract
Dockerfile.evaluator    — builds the chainml-evaluator Docker image

templates/          — all HTML pages
datasets/           — uploaded CSV datasets
models/             — saved model files
uploads/            — temporary upload staging
chainml.db          — SQLite database
```

---

## Testing it yourself

Generate datasets (uses scikit-learn built-in data):
```
python generate_datasets.py
```

Train models:
```
python train_models.py
```

This gives you iris.csv, wine.csv, breast_cancer.csv and matching .pkl files. Upload the CSV when creating a project, then submit the matching pkl. Don't mix them — a model trained on iris won't work on wine data.

---

## What each page does

| Page | What it does |
|------|-------------|
| Home | Lists all projects |
| New Project | Upload a CSV dataset, create a project |
| Submit | Upload your .pkl, server evaluates it |
| Leaderboard | Rankings by server-verified accuracy |
| Chain | Every block with its hashes and Etherscan links |
| Verify | Re-hashes the stored file, checks against the blockchain record |
| Profile | Your projects and all your submissions |

---

## Things I ran into while building this

**Ethereum mock vs real** — The app runs in mock mode if you forget to set env vars. Took me a while to figure out why submissions showed "Mock" even after setting variables — turned out Flask's auto-reloader was spawning a child process that lost the env vars. Fixed by using `run.py` to set everything before importing Flask.

**Checksum address error** — web3.py is strict about EIP-55 checksummed addresses. Got this error: `Address has an invalid EIP-55 checksum`. Fixed by passing the address through `Web3.to_checksum_address()` before using it in transactions.

**Hash mismatch on chain** — The chain verification was failing because I was using `time.time()` when computing the hash but storing a different `time.time()` value in the database. Even milliseconds apart made the hash different. Fixed by computing the timestamp once and passing that exact value to both the hash function and the database insert.

**Docker network timeout** — Building the Docker image kept timing out while downloading scikit-learn. Fixed by adding DNS servers (8.8.8.8) to Docker Desktop's engine settings, which fixed Docker's network access.

**Wrong Python path** — web3 was installed but the app couldn't find it because it was running a different Python. Fixed by adding the correct site-packages path at the top of run.py.

---

## Tech used

- Python, Flask
- SQLite
- Docker
- scikit-learn, pandas
- web3.py
- Solidity
- Ethereum Sepolia testnet
- Infura
- MetaMask
- Remix IDE