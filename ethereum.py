import hashlib, time
from config import ETHEREUM_ENABLED, INFURA_URL, DEPLOYER_ADDRESS, DEPLOYER_PRIVKEY, CONTRACT_ADDRESS

CONTRACT_ABI = [
    {"inputs": [{"internalType": "bytes32","name": "dataHash","type": "bytes32"},
                {"internalType": "string","name": "projectId","type": "string"}],
     "name": "submitModel","outputs": [],"stateMutability": "nonpayable","type": "function"},
    {"inputs": [{"internalType": "uint256","name": "index","type": "uint256"}],
     "name": "getSubmission","outputs": [{"components": [
         {"internalType": "bytes32","name": "dataHash","type": "bytes32"},
         {"internalType": "address","name": "submitter","type": "address"},
         {"internalType": "uint256","name": "timestamp","type": "uint256"},
         {"internalType": "string","name": "projectId","type": "string"}],
         "internalType": "struct ModelRegistry.Submission","name": "","type": "tuple"}],
     "stateMutability": "view","type": "function"}
]

def anchor_to_ethereum(combined_hash, project_id):
    if ETHEREUM_ENABLED:
        try:
            return _real_anchor(combined_hash, project_id)
        except Exception as e:
            print(f"[ETH] Real anchor failed: {e} — using mock")
    return _mock_anchor(combined_hash, project_id)

def _real_anchor(combined_hash, project_id):
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Infura")
    
    checksum_address = Web3.to_checksum_address(DEPLOYER_ADDRESS)
    
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)
    hash_bytes = bytes.fromhex(combined_hash)
    nonce = w3.eth.get_transaction_count(checksum_address)
    tx = contract.functions.submitModel(hash_bytes, str(project_id)).build_transaction(
        {"from": checksum_address, "nonce": nonce, "gas": 200000, "gasPrice": w3.eth.gas_price})
    signed = w3.eth.account.sign_transaction(tx, private_key=DEPLOYER_PRIVKEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    return tx_hash, f"https://sepolia.etherscan.io/tx/{tx_hash}", "real"

def _mock_anchor(combined_hash, project_id):
    raw = f"mock-{combined_hash}-{project_id}-{time.time()}"
    fake_tx = "0x" + hashlib.sha256(raw.encode()).hexdigest()
    return fake_tx, f"https://sepolia.etherscan.io/tx/{fake_tx}", "mock"
