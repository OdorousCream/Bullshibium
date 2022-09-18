from TxBlock import TxBlock
from Wallet import Wallet
from Signature import load_pub, load_priv
import NameDB.NameDB as db

class User:
    def __init__( self
                , ledger : TxBlock
                , username : str
                , password : str
                , initial_balance = 0.00
                , local_wallet = True
                ):
        self.ledger = ledger
        self.username = username
        self.password = password
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.local_wallet = local_wallet
        self.memory_wallet = None
        if self.password:
            self.public_key_on_user = self.wallet.public
        if local_wallet and password:
            Wallet.get_wallet(ledger, password, initial_balance)
    
    def refill_balance(self):
        self.current_balance = Wallet.get_balance(self.public_key, self.ledger)
    
    @property
    def balance(self):
        if self.password:
            return self.wallet.balance
        else:
            self.refill_balance()
            return self.current_balance
    
    @property
    def has_correct_password(self):
        return self.wallet.has_password(self.password)

    @property
    def public_key(self):
        if self.password:
            return self.wallet.get_raw_pub()
        else:
            try:
                return db.name_to_key(self.username)
            except:
                return load_pub(self.public_key_on_user)
    
    @property
    def private_key(self):
        return load_priv(self.wallet.private, self.password)
    
    @property
    def wallet(self):
        if self.local_wallet:
            return Wallet.get_wallet(self.ledger, self.password, self.initial_balance)
        else:
            if self.memory_wallet: return self.memory_wallet
            else:
                tmpPriv, tmpPub = Wallet.get_new_keys(self.password)
                tmpWallet = Wallet(tmpPriv, tmpPub, self.initial_balance)
                self.memory_wallet = tmpWallet
                return tmpWallet