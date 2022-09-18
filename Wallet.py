import pickle
import os

from Signature import *
from Transaction import Input, Output, Tx
from TxBlock import TxBlock

wallet_file : str = "wallet.dat"

class Wallet:
    def __init__(self, private : bytes, public : bytes, initial_balance = 0.00):
        self.private = private
        self.public = public
        self.initial_balance = initial_balance
        self.balance = initial_balance

    def make_reward(self, coins : float, pw : str):
        reward = Tx()
        reward.add_output(self.get_raw_pub(), coins)
        reward.sign(load_priv(self.private, pw))
        self.balance += coins
        return reward
    
    def make_transaction( self
                        , coins : float
                        , destination : rsa.RSAPublicKey
                        , pw : str
                        , fee : float = 0.00):
        transaction = Tx()
        transaction.add_input(self.get_raw_pub(), coins)
        if fee > 0:
            transaction.add_input(self.get_raw_pub() ,fee)
        self.balance -= coins + fee
        transaction.add_output(destination, coins)
        transaction.sign(load_priv(self.private, pw))
        return transaction
    
    def is_transaction_possible(self, coins):
        return self.balance - coins >= 0
 
    def process_input(self, input : Input):
        self.balance -= input.amount
    
    def process_output(self, output : Output):
        self.balance += output.amount

    def get_raw_pub(self):
        return load_pub(self.public)
    
    def has_password(self, pw):
        try:
            load_priv(self.private, pw)
            return True
        except:
            return False
    
    def save(self):
        tmpWallet = Wallet(self.private, self.public, self.initial_balance)
        with open(wallet_file, 'wb') as f:
            pickle.dump(tmpWallet, f)
    
    def fill_balance(self, ledger):
        self.balance = self.initial_balance
        current = ledger.get_genesis()  
        self.balance += Wallet.process_transactions(self.get_raw_pub(), current)  
        while current.next_block:
            self.balance += self.process_transactions( self.get_raw_pub()
                                                     , current.next_block)
            current = current.next_block
    
    @staticmethod
    def get_balance(public, ledger):
        balance = 0
        current = ledger.get_genesis()
        balance += Wallet.process_transactions(public, current)  
        while current.next_block:
            balance += Wallet.process_transactions( public
                                                  , current.next_block
                                                  )
            current = current.next_block
        if balance < 0: balance = 0
        return balance
    
    @staticmethod
    def process_transactions(public : rsa.RSAPublicKey, block : TxBlock):
        balance_change = 0
        for transaction in block.data:
            for input in transaction.inputs:
                if load_pub(input.address).public_numbers() \
                == public.public_numbers():
                    balance_change -= input.amount
            for output in transaction.outputs:
                if load_pub(output.address).public_numbers() \
                == public.public_numbers():
                    balance_change += input.amount
        return balance_change
    
    @staticmethod
    def save_with_name(name):
        tmpWallet = Wallet.load()
        tmpWallet.balance = tmpWallet.initial_balance
        with open(f"{name}_{wallet_file}", 'wb') as f:
            pickle.dump(tmpWallet, f)
    
    @staticmethod
    def remove_current():
        os.remove(wallet_file)
    
    @staticmethod
    def load():
        with open(wallet_file, 'rb') as f:
            return pickle.load(f)
    
    @staticmethod
    def load_with_name(name):
        with open(f"{name}_{wallet_file}", 'rb') as f:
            tmpWallet = pickle.load(f)
            tmpWallet.save()
    
    @staticmethod
    def get_new_keys(pw : str):
        tmpPriv, tmpPub = generate_keys()
        return(ser_priv(tmpPriv, pw), ser_pub(tmpPub))
    
    @staticmethod
    def get_wallet(ledger, pw, initial_balance = 0.00, wallet = None):
        if not ledger: raise Exception("wtf")
        if wallet and  Wallet.wallet_present: return wallet
        try:
            wallet = Wallet.load()
            wallet.fill_balance(ledger)
            return wallet
        except:
            tmpPriv, tmpPub = Wallet.get_new_keys(pw)
            tmpWallet = Wallet(tmpPriv, tmpPub, initial_balance)
            tmpWallet.save()
            return tmpWallet
    
    @staticmethod
    def wallet_present():
        return os.path.exists(wallet_file)
    
    @staticmethod
    def get_wallet_pub():
        tmpWallet = Wallet.load()
        return load_pub(tmpWallet.public)