from collections import namedtuple
from cryptography.hazmat.primitives.serialization import PrivateFormat, PublicFormat, Encoding, NoEncryption

from State import *
from User import *
from Session import *

Result  = namedtuple( typename = 'Result'
                    , field_names = ['ok', 'error']
                    , defaults = [None, None]
                    )

class App:
    def __init__(self):
        self.session = None
    
    def start(self):
        self.state = State.get_state()
    
    def login(self, username, password):
        if not self.state.has_user(username):
            return Result(error = f"Found no user with username {username}.")
        if Wallet.wallet_present:
            tmpPub = Wallet.get_wallet_pub()
            if not self.state.name_matches_key(username, tmpPub):
                return Result(error = f"Public key found for user {username} " \
                                    +  "doesn't match public key of current "  \
                                    +  "wallet.dat file.")
        if not self.state.check_password(username, password):
            return Result(error = f"Invalid password for user {username}.")
        user = self.state.user_from_name(username)
        user.password = password
        self.session = Session(user = user, state = self.state)
        return Result(ok = "Logged in succesfully.")
    
    def logout(self):
        self.state.save()
        self.session = None
    
    def register(self, username, password):
        if not self.state.has_user(username):
            self.state.add_user(username, password)
            return Result(ok = "Registered sucessfully")
        return Result(error = f"Username {username} is already taken.")
    
    def logout(self):
        if self.session:
            self.state = self.session.state
            self.session = None
            return Result(ok = "Logged out succesfully.")
        else:
            return Result(error = "Found no session to log out from.")
    
    def undo_transaction(self, index):
        len_before = len(self.state.unprocessed_transactions)
        self.state.undo_transaction(self.session.user.public_key, index)
        len_after = len(self.state.unprocessed_transactions)
        if len_after < len_before:
            return Result(ok = "Successfully removed transaction.")
        else:
            return Result(error = "Failed to remove transaction, are you sure it is yours?.")
    
    def show_users(self):
        return "\n".join(
            f"User: {u.username}, Balance: {u.balance} BSM" for u in self.state.get_users()
        )
    
    def show_transactions(self):
        return self.state.get_all_details()
    
    def show_pool(self):
        return self.state.get_unprocessed_details()
    
    def show_keys(self):
        if self.session:
            pub = self.session\
                      .user\
                      .public_key\
                      .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)\
                      .decode('utf8')\
                      .split('\n')\
                      [1:-2]
            
            priv = self.session\
                       .user\
                       .private_key\
                       .private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())\
                       .decode('utf8')\
                       .split('\n')\
                       [1:-2]

            n = '\n'
            return f"Public key:\n\n{n.join(pub)}\n\n" + \
                   f"Private key:\n\n{n.join(priv)}"

    def save_state(self):
        self.state.save()
        if self.session: 
            self.session.user.wallet.save()