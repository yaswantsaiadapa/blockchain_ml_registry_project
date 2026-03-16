import sys
sys.path.insert(0, r"C:/Users/yaswa/OneDrive/Desktop/python practice/Lib/site-packages")

import os
os.environ["INFURA_URL"]       = "https://sepolia.infura.io/v3/97009b43efc84fbe93ddf41e28ca66a3"
os.environ["DEPLOYER_ADDRESS"] = "0x665cc7dcb8549a4464fb324786ac96fe8469e386"
os.environ["DEPLOYER_PRIVKEY"] = "ff614e89eecf94b6add116dcd9607ad68e3ba0c785e78930cd42f05b41d41390"
os.environ["CONTRACT_ADDRESS"] = "0x9057495394eB00c9C26A2EB45893F1fcC8A010b2"

from web3 import Web3
w3 = Web3(Web3.HTTPProvider(os.environ["INFURA_URL"]))
print("="*40)
print("web3 installed: YES")
print("Sepolia connected:", w3.is_connected())
print("="*40)

from app import app
app.run(debug=False, port=5000)