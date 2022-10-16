import socket
import threading
import struct
import pickle
from time import sleep

from Signature import ser_pub

class Networker:
    def __init__(self):
        self.socket_lsn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_lsn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_snd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_snd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_rcv = None
        self.connected = False
        self.ips = ["192.168.122.75"] #, "192.168.122.135"]
    
    def listen(self, state):
        if not self.connected:
            self.socket_lsn.bind(('', 65432))
            self.socket_lsn.listen()
            self.socket_rcv, addr = self.socket_lsn.accept()
            # with conn:
            print(f"Connected by {addr}")
            self.connected = True
            while True:
                msg = self.recv_msg()
                if not msg:
                    break
                self.handle_msg(msg, addr, state)
        else:
            addr = self.socket.getpeername()
            print(f"Connected by {addr}")
            while True:
                msg = self.recv_msg()
                if not msg:
                    break
                self.handle_msg(msg, addr, state)
    
    def start_listener(self, state):
        threading.Thread(target = self.listen, args = (state,)).start()
    
    def connect(self, ip):
        self.socket_snd.connect((ip, 65432))
        print(f"Established connection with {ip}")
        self.connected = True
    
    def send_msg(self, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        retries = 0
        while retries < 3 and self.connected:
            try:
                self.socket_snd.sendall(msg)
            except BrokenPipeError:
                sleep(0.25)
                retries += 1

    def send_msg_of_kind(self, msg, kind):
        while not self.connected:
            try:
                self.connect(self.ips[0])
            except:
                print(f"Trying to connect to {self.ips[0]}") 
                sleep(1)
        print(f"Sending message of kind {kind} to {self.ips[0]}")
        message = pickle.dumps((kind, msg))
        self.send_msg(message)
    
    def recv_msg(self):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(self.socket_rcv, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(self.socket_rcv, msglen)

    def recvall(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def handle_msg(self, payload, received_from, state):
        payload = pickle.loads(payload)
        print(f"Received message {payload}")
        label = payload[0]
        msg = payload[1]

        print(f"\nReceived message {msg} from {received_from}\n")

        # def update_ips():
        #     # Update the other node with any additional ips that we know of
        #     other_node_ips = payload[2]
        #     own_ips = [ip for ip in state.get_ips() if ip != received_from]
        #     ips_to_add = [ip for ip in own_ips if ip not in other_node_ips]
        #     for ip in ips_to_add:
        #         self.send_ip(ip, [received_from])

        # if label == "transaction":
        #     state.add_transaction(msg)
        # if label == "ip":
        #     state.add_ip(msg)
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
            curr_users = state.get_users()
            new_received = [user for user in msg if not user in curr_users]
            for user in new_received:
                state.add_user_obj(user, user.public_key_on_user)
        if label == "req_ledger":
            self.send_ledger(state.ledger)
        if label == "req_users":
            "Handling req users"
            users = state.get_users()
            for user in users:
                user.public_key_on_user = ser_pub(user.public_key)
            self.send_users(users)


    def request_ledger(self):
        self.send_msg_of_kind(b'0', "req_ledger")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (b'0', "req_ledger", ips)).start()

    def request_users(self):
        self.send_msg_of_kind(b'0', "req_users")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (b'0', "req_users", ips)).start()

    def send_users(self, msg):
        self.send_msg_of_kind(msg, "users")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (msg, "users", ips)).start()

    def send_ledger(self, msg):
        self.send_msg_of_kind(msg, "ledger")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (msg, "ledger", ips)).start()

    def send_transaction(self, msg):
        self.send_msg_of_kind(msg, "transaction")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (msg, "transaction", ips)).start()

    def send_ip(self, msg):
        self.send_msg_of_kind(msg, "ip")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (msg, "ip", ips)).start()

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
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (user, "user", ips)).start()

    def send_rem_transaction(self, msg, ips):
        self.send_msg_of_kind(msg, "transaction_rem")
        # threading.Thread( target = send_msg_of_kind
        #                 , args = (msg, "transaction_rem", ips)).start()