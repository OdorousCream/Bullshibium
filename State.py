from threading import Lock
import uuid
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from datetime import datetime, timedelta
from getch import getch
from time import sleep

from typing import List
from TxBlock import TxBlock
from Transaction import *
from NetworkerSocket import *
from User import User
import NameDB.NameDB as db

class State:
    def __init__(self):
        self.ledger : TxBlock = TxBlock.load()
        self.lock = Lock()
        self.networker = None
    
    def start_networker(self):
        if not self.networker == None: return
        self.networker = Networker()
        self.networker.start_listener(self)
    
    # def stop_networker(self):
    #     if self.networker == None: return
    #     self.networker.stop_listening()
    #     self.networker = None
    
    @property
    def unprocessed_transactions(self):
        return self.ledger.unprocessed_transactions
    
    def add_user_obj( self
                    , user: User
                    , public_key
                    ):
        self.lock.acquire()
        db.add_pair(user.username, load_pub(public_key))
        # send_user(user, public_key, self.get_ips())
        self.lock.release()
    
    def add_user( self
                , username : str
                , password : str
                , initial_balance = 0.00
                , local_wallet = True
                , send_through_network = True
                ):
        
        user = User(self.ledger, username, password, initial_balance, local_wallet)
        self.add_user_obj(user, user.wallet.public)
        if send_through_network:
            self.networker.send_user(user, user.wallet.public)
    
    def add_and_get_user( self
                        , username : str
                        , password : str
                        , initial_balance = 0.00
                        , local_wallet = True
                        , send_through_network = True
                        ):
        user = User(self.ledger, username, password, initial_balance, local_wallet)
        self.add_user_obj(user, user.wallet.public)
        if send_through_network:  
            self.networker.send_user(user, user.wallet.public)
        return user
    
    def add_ip(self, ip):
        if db.has_ip(ip): return
        self.lock.acquire()
        db.add_ip(ip)
        self.lock.release()
    
    @staticmethod
    def get_ips():
        return db.get_all_ips()

    def get_users(self):
        tmpUsers = [User(self.ledger, pair.name, "") for pair in db.get_all_pairs()]
        for user in tmpUsers: 
            user.refill_balance()
        return tmpUsers
    
    def get_nondefault_users(self):
        return [u for u in self.get_users() if u.username not in ["Melon Husk", "Bitter"]]
    
    def has_user(self, username : str):
        return db.has_name(username)
    
    def name_matches_key(self, username : str, key : RSAPublicKey):
        return db.name_has_key(username, key)
    
    def check_password(self, username : str, password : str):
        user = self.user_from_name(username)
        user.password = password
        return user.has_correct_password
    
    def key_from_name(self, username : str):
        return db.name_to_key(username)
    
    def name_from_key(self, pub_key : RSAPublicKey):
        return db.key_to_name(pub_key)

    def user_from_key(self, pub_key : RSAPublicKey) -> User:
        username = db.key_to_name(pub_key)
        return self.user_from_name(username)

    def user_from_name(self, username : str) -> User:
        return User(self.ledger, username, "")

    def add_transaction(self, transaction : Tx, send_through_network = True):
        self.lock.acquire()
        self.unprocessed_transactions.append(transaction)
        if send_through_network:
            self.networker.send_transaction(transaction)
        self.lock.release()
    
    def remove_transaction(self, item):
        self.lock.acquire()
        self.unprocessed_transactions.remove(item)
        self.networker.send_rem_transaction(item)
        self.lock.release()
    
    def undo_transaction(self, public : RSAPublicKey, index : int):
        self.lock.acquire()
        tmp_transaction = self.unprocessed_transactions[index]
        if load_pub(tmp_transaction.reqd[0]).public_numbers() == public.public_numbers():
            self.remove_transaction(self.unprocessed_transactions[index])
            self.networker.send_rem_transaction(self.unprocessed_transactions[index])
        self.lock.release()
    
    def add_block(self, time):
        tmpUnprocessed = self.unprocessed_transactions
        tmpBlock = TxBlock(time_added = time) if not self.ledger.data \
              else TxBlock(self.ledger, time_added = time)
        for transaction in tmpUnprocessed:
            tmpBlock.addTx(transaction)
        self.ledger = tmpBlock

    def mine(self, user : User):
        difficulty = 0 if user.username == "Melon Husk" else 2
        mining_reward = 54.20
        if not len(self.unprocessed_transactions) >= 9: raise Exception("Mining not possible")
        for t in self.unprocessed_transactions:
            if t.total_in > t.total_out:
                mining_reward += t.total_in - t.total_out
        if self.ledger:
            tmp_first_valid = self.ledger.get_first_valid()
        if self.ledger and tmp_first_valid:
            self.ledger = tmp_first_valid
        tmpTransaction = user.wallet.make_reward(mining_reward, user.password)
        self.add_transaction(tmpTransaction)
        self.networker.send_transaction(tmpTransaction)
        time = datetime.now()
        if  self.ledger.previous_block \
        and self.ledger.previous_block.time_added \
        and self.ledger.previous_block.time_added + timedelta(minutes = 3) >= time:
            raise Exception("Too soon to add another block.")
        self.add_block(time)
        self.ledger.mine(difficulty)
        if not self.ledger.is_valid():
            self.ledger = self.ledger.get_first_valid()
            raise Exception("Mining failed")
        user.refill_balance()
        self.save()
        self.networker.send_ledger(self.ledger)
        print(f"Got {mining_reward} BSM as reward for mining.\n")
    
    def fill_detail(self, detail : Detail) -> str:
        keys = [load_pub(key) for key in detail.pub_keys]
        names = [self.user_from_key(key).username for key in keys]
        return detail.text.format(*names)
    
    def get_unprocessed_details(self) -> str:
        return self.get_transaction_details(self.unprocessed_transactions)
    
    def get_block_details(self, block : TxBlock) -> str:
        return f"BLOCK {block.id}\n\n"\
               + self.get_transaction_details(block.data)
    
    def get_transaction_details(self, transactions : List[Tx]):
        details = []
        for i, transaction in enumerate(transactions):
            transaction_details = [self.fill_detail(detail) for detail in transaction.get_details()]
            details.append(f"{i}:-----------------------\n"  \
                          + "\n".join(transaction_details) \
                          + "\n-------------------------\n"
                          )
        return "\n".join(details)

    def get_all_details(self):
        details = []
        current = self.ledger.get_genesis()
        details.append(self.get_block_details(current))
        while current.next_block:
            details.append(self.get_block_details(current.next_block))
            current = current.next_block
        return "\n\n-------------------------\n\n".join(details)
    
    def save(self):
        self.ledger.save()
    
    def request(self):
        self.networker.request_users()
        self.networker.request_ledger()
        sleep(2)
        print("\nRequesting state from network\n")
        print("Press any key to continue-")
        getch()
    
    @staticmethod
    def load():
        tmpState = State()
        tmpState.add_ip("192.168.122.183")
        tmpState.add_ip("192.168.122.102")
        return tmpState

    @staticmethod
    def get_initial_state():
        melon_husk_name = "Melon Husk"
        bitter_name = "Bitter"
        sold_lattes = 10 * 54.20
        tmpState = State()

        melon_husk = \
            tmpState.add_and_get_user( melon_husk_name
                                     , str(uuid.uuid4())
                                     , initial_balance = sold_lattes
                                     , local_wallet = False
                                     , send_through_network = False
                                     )

        bitter = \
            tmpState.add_and_get_user( bitter_name
                                     , str(uuid.uuid4())
                                     , local_wallet = False
                                     , send_through_network = False
                                     )

        while melon_husk.wallet.is_transaction_possible(54.20):
            tmpTransaction = melon_husk.wallet \
                                    .make_transaction( 54.20
                                                     , bitter.public_key
                                                     , melon_husk.password
                                                     )
            tmpState.add_transaction(tmpTransaction, send_through_network=False)
        
        return tmpState
    
    @staticmethod
    def get_state():
        tmpState = State.load()
        if not tmpState.ledger.unprocessed_transactions \
       and not tmpState.ledger.data \
       and not tmpState.ledger.previous_block:
            tmpState = State.get_initial_state()
            tmpState.save()
        tmpState.start_networker()
        tmpState.request()
        return tmpState