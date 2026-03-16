# Ethereum Sepolia Setup Guide
## Step-by-step to connect ChainML to a real public blockchain

---

## What You Need (all free)

- MetaMask browser extension
- Infura account (free)
- ~0.1 Sepolia ETH (free from faucet)
- Remix IDE (browser-based, no install)

---

## STEP 1 — Install MetaMask

1. Go to https://metamask.io
2. Click "Download" and install the browser extension
3. Create a new wallet — write down your 12-word seed phrase and keep it safe
4. Your wallet address looks like: 0xABCD...1234 — copy it, you'll need it

---

## STEP 2 — Add Sepolia Testnet to MetaMask

1. Open MetaMask
2. Click the network dropdown at the top (shows "Ethereum Mainnet")
3. Click "Add network" → "Add a network manually"
4. Fill in:
   - Network name:    Sepolia Test Network
   - RPC URL:         https://rpc.sepolia.org
   - Chain ID:        11155111
   - Currency symbol: ETH
   - Block explorer:  https://sepolia.etherscan.io
5. Click Save — switch to Sepolia network

---

## STEP 3 — Get Free Sepolia ETH

You need fake ETH to pay gas fees for deploying and calling the contract.

1. Go to https://sepoliafaucet.com
2. Connect your MetaMask wallet
3. Click "Send me ETH"
4. Wait 1-2 minutes — you'll receive 0.5 Sepolia ETH
5. Confirm in MetaMask — you should see the balance

Alternative faucet if the above is slow: https://faucet.sepolia.dev

---

## STEP 4 — Get a Free Infura API Key

Infura gives your Flask app an API endpoint to talk to Ethereum without running a node.

1. Go to https://infura.io and create a free account
2. Click "Create New API Key"
3. Select "Web3 API" as the network
4. Name it "ChainML"
5. Click Create
6. Go to your new project — copy the API key (looks like: abc123def456...)
7. Your Infura URL will be:
   https://sepolia.infura.io/v3/YOUR_API_KEY

---

## STEP 5 — Deploy the Smart Contract

1. Go to https://remix.ethereum.org (no install needed)
2. In the file explorer on the left, create a new file: ModelRegistry.sol
3. Copy the entire contents of ModelRegistry.sol from this project into it
4. Click the Solidity compiler tab (second icon on left sidebar)
   - Set compiler version to 0.8.19
   - Click "Compile ModelRegistry.sol"
   - You should see a green checkmark
5. Click the Deploy & Run tab (third icon)
   - Environment: select "Injected Provider - MetaMask"
   - MetaMask will pop up — connect it and select Sepolia network
   - Contract: select "ModelRegistry"
   - Click the orange "Deploy" button
   - MetaMask will ask to confirm the transaction — click Confirm
   - Wait 10-30 seconds for the transaction to be mined
6. In the "Deployed Contracts" section below, you'll see your contract
7. Copy the contract address (looks like: 0xDEF...5678)
   This is your CONTRACT_ADDRESS

---

## STEP 6 — Get Your Private Key from MetaMask

WARNING: Never share your private key with anyone. Use a dedicated wallet for this, not your main wallet.

1. Open MetaMask
2. Click the three dots next to your account name
3. Click "Account details"
4. Click "Export private key"
5. Enter your MetaMask password
6. Copy the private key (64 hex characters, no 0x prefix needed)

---

## STEP 7 — Set Environment Variables

Before running app.py, set these four environment variables in your terminal:

On Mac/Linux:
  export INFURA_URL="https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
  export DEPLOYER_ADDRESS="0xYOUR_WALLET_ADDRESS"
  export DEPLOYER_PRIVKEY="YOUR_PRIVATE_KEY_WITHOUT_0x"
  export CONTRACT_ADDRESS="0xYOUR_DEPLOYED_CONTRACT_ADDRESS"

On Windows (Command Prompt):
  set INFURA_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
  set DEPLOYER_ADDRESS=0xYOUR_WALLET_ADDRESS
  set DEPLOYER_PRIVKEY=YOUR_PRIVATE_KEY_WITHOUT_0x
  set CONTRACT_ADDRESS=0xYOUR_DEPLOYED_CONTRACT_ADDRESS

Then run: python app.py

---

## STEP 8 — Install web3.py

  pip install web3

---

## STEP 9 — Verify It's Working

1. Start the app: python app.py
2. In the terminal you should see: Ethereum enabled: True
3. Create a project, submit a model
4. On the result page you'll see a real Etherscan link
5. Click it — you'll see the transaction on the live Sepolia blockchain
6. The hash stored there matches the combined_hash in your SQLite DB

---

## How to Verify a Hash Manually (Option B — no server needed)

1. Get the model.pkl file
2. Run this Python command:
   python3 -c "import hashlib; h=hashlib.sha256(); h.update(open('model.pkl','rb').read()); print(h.hexdigest())"
3. Go to https://sepolia.etherscan.io
4. Search for the transaction hash from the project's chain page
5. Click "Input Data" — decode it
6. You'll see the combined_hash stored on-chain
7. Compare manually — no trust in the website needed

---

## Mock Mode (no Ethereum setup)

If you don't set the environment variables, the app runs in Mock Mode:
- Everything works exactly the same
- Fake transaction hashes are generated deterministically
- Etherscan links look real but point to non-existent transactions
- Perfect for local demo and development

To switch to real mode later, just set the 4 environment variables and restart.

---

## Cost Summary

| Item           | Cost     |
|----------------|----------|
| MetaMask       | Free     |
| Infura API key | Free     |
| Sepolia ETH    | Free     |
| Contract deploy| ~$0      |
| Each submission| ~$0      |
| Everything     | FREE     |

Sepolia is a testnet — no real money involved.
