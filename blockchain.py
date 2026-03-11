import hashlib
import json
import time
from hash_utils import hash_dict


class Block:
    def __init__(self, index, data, previous_hash="0"):
        self.index = index
        self.timestamp = time.time()
        self.data = data          # dict: username, model_name, accuracy, model_hash, filepath
        self.previous_hash = previous_hash
        self.hash = self._compute_hash()

    def _compute_hash(self):
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        return hash_dict(block_content)

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class Blockchain:
    def __init__(self):
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(0, {"info": "Genesis Block"}, "0")
        self.chain.append(genesis)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data: dict):
        new_block = Block(
            index=len(self.chain),
            data=data,
            previous_hash=self.get_latest_block().hash,
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current._compute_hash():
                return False, f"Block {i} hash mismatch"
            if current.previous_hash != previous.hash:
                return False, f"Block {i} broken link"
        return True, "Chain is valid"

    def find_block_by_model(self, model_hash: str):
        for block in self.chain[1:]:
            if block.data.get("model_hash") == model_hash:
                return block
        return None

    def get_best_model(self):
        best = None
        best_acc = -1
        for block in self.chain[1:]:
            acc = block.data.get("accuracy", 0)
            if acc > best_acc:
                best_acc = acc
                best = block
        return best

    def to_list(self):
        return [b.to_dict() for b in self.chain]
