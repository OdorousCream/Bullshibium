from typing_extensions import Self
from cryptography.hazmat.primitives.hashes import Hash, SHA256
from pickle import dumps as serialize

from typing import List
from Transaction import Tx

class CBlock:
    previous_block = None
    next_block = None
    data : List[Tx] = []
    nonce = None
    hash = None
    
    def __init__(self, data : List[Tx], previous_block):
        self.data = data
        if previous_block != None:
            self.previous_block = previous_block
            self.previous_block.next_block = self
    
    @property
    def id(self):
        if self.previous_block: return self.previous_block.id + 1
        else: return 0
    
    def computeHash(self, nonce):
        hash = Hash(SHA256())
        if self.previous_block != None:
            hash.update(serialize(self.previous_block.hash))
        hash.update(serialize(self.data))
        hash.update(serialize(nonce))
        return hash.finalize()
        
    def mine(self, leading_zeros):
        leading_zeros = leading_zeros * b'0'
        nonce = 0
        hash = b''
        print("Mining...\n")
        while not hash.startswith(leading_zeros):
            hash = self.computeHash(nonce)
            nonce += 1
            print(f"Hash: {hash}, Nonce: {nonce}\n")
        self.hash = self.computeHash(nonce)
        self.nonce = nonce
        print(f"Mining succesful!\nFound hash {hash} with nonce {nonce}.")

    def is_valid_hash(self):
        currentValid = self.computeHash(self.nonce) == self.hash
        if not self.previous_block: return currentValid
        else: return currentValid and self.previous_block.is_valid_hash()
    
    def get_first_valid(self):
        currentValid = self.is_valid()
        if not currentValid and not self.previous_block: return None
        return self if currentValid else self.previous_block.get_first_valid()
    
    def get_genesis(self) -> Self:
        if not self.previous_block: return self
        else: return self.previous_block.get_genesis()