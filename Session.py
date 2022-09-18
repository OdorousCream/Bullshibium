from State import State
from User import User

class Session:
    def __init__(self, user : User, state : State):
        self.user = user
        self.state = state
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.state.save()
        self.user.wallet.save()