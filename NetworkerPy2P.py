from pyp2p.net import *
import threading
import pickle
from getch import getch

from Signature import ser_pub

rendezvous_servers = [
    {
        "addr": "192.168.122.38",
        "port": 8000
    }
]

own_ip = "192.168.122.102"
port_used = 44444

class Networker:

    def __init__(self):
        self.node = Net(passive_bind=own_ip, passive_port=port_used, node_type="passive", debug=1, servers=rendezvous_servers)
        self.node.start()
        self.node.bootstrap()
        self.node.advertise()
        self.listener = None

    def start_listening(self, state):
        self.listener = threading.Thread( target=self.listen, args={state,}).start()
    
    def stop_listening(self):
        if self.listener:
            self.listener.kill()
            self.listener.join()
        self.node.stop()
    
    def send_msg(self, msg):
        for con in self.node:
            con.send_line(msg)
            time.sleep(1)

    def send_msg_of_kind(self, msg, kind):
        # print(f"Sending message of kind {kind} to {ips[0]}")
        # getch()
        message = pickle.dumps((kind, msg))
        self.send_msg(message.hex())
    
    def listen(self, state):
        while True:
            for con in self.node:
                for reply in con:
                    self.handle_msg(reply, state)

            time.sleep(1)
    
    def handle_msg(self, payload, state):
        # payload = payload.encode("ascii")
        # payload = payload.decode("latin1")
        payload = bytes.fromhex(payload)
        payload = pickle.loads(payload)
        print(f"Received message {payload}")
        label = payload[0]
        msg = payload[1]

        print(f"\nReceived message {msg}\n")
        getch()

        # def update_ips():
        #     # Update the other node with any additional ips that we know of
        #     other_node_ips = payload[2]
        #     own_ips = [ip for ip in state.get_ips() if ip != received_from]
        #     ips_to_add = [ip for ip in own_ips if ip not in other_node_ips]
        #     for ip in ips_to_add:
        #         self.send_ip(ip, [received_from])

        if label == "transaction":
            state.add_transaction(msg, send_through_network = False)
        if label == "ip":
            state.add_ip(msg)
        # if label == "block":
        #     state.lock.acquire()
        #     ledger_before = state.ledger
        #     ledger_after = payload[3]
        #     state.add_block(msg)
        #     if state.ledger != ledger_after:
        #         if ledger_after.is_valid():
        #             state.ledger = ledger_after
        #         else:
        #             state.ledger = ledger_before
        #     state.lock.release()

        if label == "user":
            users = state.get_users()
            received_user = msg
            if not any(user.username == received_user.username for user in users):
                state.add_user_obj(msg, msg.public_key_on_user)
        if label == "transaction_rem":
            state.remove_transaction(msg)
        if label == "ledger" and msg.is_valid():
            state.lock.acquire()
            state.ledger = msg
            state.lock.release()
        if label == "users":
            curr_users = state.get_nondefault_users()
            new_received = [user for user in msg if not user in curr_users]
            for user in new_received:
                state.add_user_obj(user, user.public_key_on_user)
        if label == "req_ledger":
            self.send_ledger(state.ledger)
        if label == "req_users":
            users = state.get_users()
            for user in users:
                user.public_key_on_user = ser_pub(user.public_key)
            self.send_users(users)
    
    def request_ledger(self):
        self.send_msg_of_kind(b'0', "req_ledger")

    def request_users(self):
        self.send_msg_of_kind(b'0', "req_users")

    def send_users(self, msg):
        self.send_msg_of_kind(msg, "users")

    def send_ledger(self, msg):
        self.send_msg_of_kind(msg, "ledger")

    def send_transaction(self, msg):
        self.send_msg_of_kind(msg, "transaction")

    def send_ip(self, msg):
        self.send_msg_of_kind(msg, "ip")

    # def send_mined_block(msg, ips, ledger_after):
    #     own_ip = socket.gethostbyname(socket.gethostname())
    #     ips = [ip for ip in ips if ip != own_ip]
    #     msg = pickle.dumps(("block", msg, ips, ledger_after))
    #     for ip in ips:
    #         try:
    #             socketer.connect((ip, 5005))
    #             send_msg(socketer, msg)
    #         except:
    #             pass

    def send_user(self, user, pub_key):
        user.public_key_on_user = pub_key
        self.send_msg_of_kind(user, "user")

    def send_rem_transaction(self, msg):
        self.send_msg_of_kind(msg, "transaction_rem")