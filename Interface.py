import re
from pyfiglet import Figlet
from getch import getch
import os

from App import *

class Interface:
    def __init__(self):
        self.user = None
    
    def get_user(self):
        user = self.app.session.user
        user.refill_balance()
        return user

    def start(self):
        self.app = App()
        self.app.start()
        while True:
            self.clear()
            self.renderlogo()
            if not self.app.session:
                print("Welcome to the Bullshibium network!")
                print("Press 1 to log in")
                print("Press 2 to register")
                print("Press 3 to load a saved wallet by username")
                print("Press q to quit")
                pressed = getch()
                if pressed == "1": 
                    self.login()
                if pressed == "2": self.register()
                if pressed == "3": self.load_wallet()
                if pressed == "q": 
                    self.app.save_state()
                    print("\nExiting the Bullshibium network...\n")
                    os._exit(1)
                continue
            
            print(f"Welcome to the BSM network, {self.user.username}!\n")
            print(f"Your current balance is {self.user.balance}\n")
            print("Press 1 to transfer BSM to another user")
            print("Press 2 to mine")
            print("Press 3 to view all users")
            print("Press 4 to view the public ledger")
            print("Press 5 to view the unprocessed transaction pool")
            print("Press 6 to view your public and private keys")
            print("Press q to log out")
            pressed = getch()
            if pressed == "1": self.transfer()
            if pressed == "2": self.mine()
            if pressed == "3": self.view_all_users()
            if pressed == "4": self.view_ledger()
            if pressed == "5": self.view_pool()
            if pressed == "6": self.view_keys()
            if pressed == "q": self.logout()

    def login(self):
        self.clear()
        self.renderlogo()

        if not Wallet.wallet_present():
            print("No wallet.dat present, login not possible.")
            print("Press 1 to continue to register instead")
            print("Press 2 to load a saved wallet by username")
            print("Press any other key to go back")
            pressed = getch()
            if pressed == "1": self.register()
            if pressed == "2": self.load_wallet()
            else: return

        username = input("Username: ")
        password = input("Password: ")
        result = self.app.login(username, password)
        if result.error: 
            print(result.error)
            print("Press any key to continue")
            getch()
            return
        self.user = self.get_user()
    
    def logout(self):
        self.clear()
        self.renderlogo()

        self.app.logout()
        print("You've been logged out")
        print("Press any key to continue")
        getch()

    def register(self):
        self.clear()
        self.renderlogo()

        if Wallet.wallet_present():
            print("There is currently a wallet.dat file present. Would you like to rename it?")
            print("Press 1 to proceed with renaming")
            print("Press any other key to go back")
            pressed = getch()
            if pressed != "1": return
            tmpPub = Wallet.get_wallet_pub()
            tmpName = self.app.state.name_from_key(tmpPub)
            Wallet.save_with_name(tmpName)
            Wallet.remove_current()

        username = input("Username: ")
        password = input("Password: ")
        if len(password) > 0:
            result = self.app.register(username, password)
            if result.error: 
                print(result.error)
                print("Press any key to continue")
                getch()
                return
            print("Successfully registered!")
        else:
            print("Password must be at least one character long.")
            getch()
            return

        print("Press any key to continue")
        getch()
        self.app.login(username, password)
        self.user = self.get_user()
    
    def load_wallet(self):
        self.clear()
        self.renderlogo()

        username = input("Username: ")
        if Wallet.wallet_present():
            tmpPub = Wallet.get_wallet_pub()
            tmpName = self.app.state.name_from_key(tmpPub)
            Wallet.save_with_name(tmpName)
            
        Wallet.load_with_name(username)
        print(f"Successfully loaded wallet, you can now log in as {username}.")
        print("Press any key to continue")
        getch()
    
    def transfer(self):
        self.clear()
        self.renderlogo()

        receiver_name = input("Receiver: ")
        if not self.app.state.has_user(receiver_name):
            print(f"No user found with name {receiver_name}")
        else:
            receiver = self.app.state.key_from_name(receiver_name)
            amount = float(input("Amount: "))
            fee = 0.00
            print("\n")
            print("Would you like to add an extra transaction fee?")
            print("Press 1 to add a fee")
            print("Press 2 to continue without adding a fee")
            while(True):
                pressed = getch()
                if pressed == "1":
                    print()
                    fee = float(input("Fee: "))
                    break
                if pressed == "2": break
            self.app.state.add_transaction(
                self.user.wallet.make_transaction( amount
                                                 , receiver
                                                 , self.user.password
                                                 , fee
                                                 )
            )
            print(f"Sent {amount} to {receiver_name}.")
            if fee > 0:
                print(f"Paid {fee} as an extra fee.")
            print(("\nThere are currently "
                  f"{len(self.app.state.unprocessed_transactions)} "
                   "transactions in the pool."))
        print("\nPress any key to continue")
        getch()
        self.app.save_state()
    
    def mine(self):
        self.clear()
        self.renderlogo()

        if len(self.app.state.unprocessed_transactions) > 0:
            if len(self.app.state.unprocessed_transactions) < 9:
                print("Not enough transactions in pool to mine")
            else:
                self.app.state.mine(self.user)
        else: print("No transactions to process")

        print("\nPress any key to continue")
        getch()
    
    def view_all_users(self):
        self.simple_page(lambda: print(self.app.show_users()))
    
    def view_ledger(self):
        self.simple_page(lambda: print(self.app.show_transactions()))

    def view_pool(self):
        self.clear()
        self.renderlogo()

        if not self.app.state.unprocessed_transactions:
            print("The pool is empty.")
            print("\nPress any key to continue")
            getch()
            return

        print("The pool contains all unprocessed transactions.")
        print("Press the number of a transaction to undo it.")
        print("Press any other key to continue.")

        print(self.app.show_pool())

        pressed = getch()
        try:
            index = int(pressed)
            result = self.app.undo_transaction(index)
            if result.error: 
                print(result.error)
                print("\nPress any key to continue")
                getch()
            if result.ok:
                print("Successfully removed transaction")
                print("\nPress any key to continue")
                getch()
        except: return
    
    def view_keys(self):
        self.simple_page(lambda: print(self.app.show_keys()))

    @staticmethod
    def simple_page(show_content):
        Interface.clear()
        Interface.renderlogo()

        show_content()

        print("\nPress any key to continue")
        getch()

    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def renderlogo():
        fig = Figlet(font='slant')
        print(fig.renderText("Bullshibium"))