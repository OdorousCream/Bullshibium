import pickle
from typing import List

from Transaction import Tx
from BlockChain import CBlock

class TxBlock (CBlock):
    
    def __init__(self, previous_block = None, time_added = None):
        super().__init__([], previous_block)
        self.unprocessed_transactions : List[Tx] = []
        self.time_added = time_added

    def addTx(self, tx : Tx):
        self.data.append(tx)
    
    def is_valid(self): 
        return self.is_valid_hash() \
        and self.transactions_valid()
    
    def transactions_valid(self):
        return all(transaction.is_valid() for transaction in self.data)
    
    def save(self):
        with open("ledger.dat", 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load():
        try:
            with open("ledger.dat", 'rb') as f:
                return pickle.load(f)
        except:
            return TxBlock()