import socket
import threading
import struct
import pickle
from time import sleep
from getch import getch

from Signature import ser_pub

class Networker:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn_socket = None
        self.connected = False
        # IP of other machine goes here
        self.ips = ["192.168.122.183", "192.168.122.102"]
    
    def listen(self, state):
        if not self.connected:
            self.socket.bind(('', 65432))
            self.socket.listen()
            self.conn_socket, addr = self.socket.accept()
            # with conn:
            print(f"Connected by {addr}")
            self.connected = True
            while True:
                msg = self.recv_msg(self.conn_socket)
                if not msg:
                    break
                self.handle_msg(msg, addr, state)
        else:
            addr = self.socket.getpeername()
            print(f"Connected by {addr}")
            while True:
                msg = self.recv_msg(self.socket)
                if not msg:
                    break
                self.handle_msg(msg, addr, state)
    
    def start_listener(self, state):
        threading.Thread(target = self.listen, args = (state,)).start()
    
    def connect(self, ip):
        self.socket.connect((ip, 65432))
        print(f"Established connection with {ip}")
        self.connected = True
    
    def send_msg(self, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        self.socket.sendall(msg)

    def send_msg_of_kind(self, msg, kind):
        own_ip = socket.gethostbyname(socket.gethostname())
        ips = [ip for ip in self.ips if ip != own_ip]
        if not self.connected:
            # self.connect(ips[0])
            return
        print(f"Sending message of kind {kind} to {ips[0]}")
        getch()
        message = pickle.dumps((kind, msg))
        self.send_msg(message)
    
    def recv_msg(self, sock):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(sock, msglen)

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
        getch()

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
            self.send_ledger(state.ledger, [received_from])
        if label == "req_users":
            "Handling req users"
            users = state.get_users()
            for user in users:
                user.public_key_on_user = ser_pub(user.public_key)
            self.send_users(users, [received_from])


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

    

# # socketee = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # socketee.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# # socketee.bind(('', 5005))
# # socketer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# # def send_msg(sock, msg):
# #     # Prefix each message with a 4-byte length (network byte order)
# #     length = len(msg)
# #     msg = struct.pack('>I', len(msg)) + msg
# #     print(f"Sending message {msg.encode('utf8')} with length {length}")
# #     print("TESTTESTTEST")
# #     sock.sendall(msg.encode('utf8'))

# # def send_msg_of_kind(msg, kind, ips):
# #     own_ip = socket.gethostbyname(socket.gethostname())
# #     ips = [ip for ip in ips if ip != own_ip]
# #     print(f"\nSending message of kind {kind} with contents:\n\t{msg}\n to all of these: {ips}\n") 
# #     msg = pickle.dumps((kind, msg, ips))
# #     for ip in ips:
# #         try:
# #             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
# #                 # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# #                 s.connect((ip, 65432))
# #                 print(f"\nSending message of kind {kind} to {ip}\n") 
# #                 send_msg(s, msg)
# #         except:
# #             pass

# # def recv_msg(sock):
# #     # Read message length and unpack it into an integer
# #     raw_msglen = recvall(sock, 4)
# #     msglen = struct.unpack('>I', raw_msglen)[0]
# #     print("msg length: ",msglen)
# #     # Read the message data
# #     return recvall(sock, msglen) 

# # def recvall(sock, n):
# #     # Helper function to recv n bytes or return None if EOF is hit
# #     data = bytearray()
# #     while len(data) < n:
# #         print(f"Receiving {n} bytes, current data is {data}")
# #         packet = sock.recv(n - len(data))
# #         if not packet:
# #             break
# #         data.extend(packet)
# #     return data

# def handle_msg(payload, received_from, state):
#     payload = pickle.loads(payload)
#     print(f"Received message {payload}")
#     label = payload[0]
#     msg = payload[1]

#     print(f"\nReceived message {msg} from {received_from}\n")
#     getch()

#     def update_ips():
#         # Update the other node with any additional ips that we know of
#         other_node_ips = payload[2]
#         own_ips = [ip for ip in state.get_ips() if ip != received_from]
#         ips_to_add = [ip for ip in own_ips if ip not in other_node_ips]
#         for ip in ips_to_add:
#             send_ip(ip, [received_from])

#     if label == "transaction":
#         state.add_transaction(msg)
#     if label == "ip":
#         state.add_ip(msg)
#     # if label == "block":
#     #     state.lock.acquire()
#     #     ledger_before = state.ledger
#     #     ledger_after = payload[3]
#     #     state.add_block(msg)
#     #     if state.ledger != ledger_after:
#     #         if ledger_after.is_valid():
#     #             state.ledger = ledger_after
#     #         else:
#     #             state.ledger = ledger_before
#     #     state.lock.release()

#     if label == "user":
#         users = state.get_users()
#         received_user = msg
#         if not any(user.username == received_user.username for user in users):
#             state.add_user_obj(msg, msg.public_key_on_user)
#     if label == "transaction_rem":
#         state.remove_transaction(msg)
#     if label == "ledger" and msg.is_valid():
#         state.lock.acquire()
#         state.ledger = msg
#         state.lock.release()
#     if label == "users":
#         curr_users = state.get_users()
#         new_received = [user for user in msg if not user in curr_users]
#         for user in new_received:
#             state.add_user_obj(user, user.public_key_on_user)
#     if label == "req_ledger":
#         update_ips()
#         send_ledger(state.ledger, [received_from])
#     if label == "req_users":
#         "Handling req users"
#         update_ips()
#         users = state.get_users()
#         for user in users:
#             user.public_key_on_user = ser_pub(user.public_key)
#         send_users(users, [received_from])

# # def listen(state):
# #     while True:
# #         print("Listening...")
# #         socketee.listen()
# #         sock, addr = socketee.accept()
# #         print(f"Received a message from {addr[0]}")
# #         getch()
# #         msg = recv_msg(sock)
# #         handle_msg(msg, addr[0], state)

# # def listen(state):
# #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
# #         s.bind(('', 65432))
# #         print("Listening...")
# #         s.listen()
# #         while True:
# #             conn, addr = s.accept()
# #             with conn:
# #                 print(f"Connected by {addr}")
# #                 while True:
# #                     msg = recv_msg(conn)
# #                     if not msg:
# #                         break
# #                     print(f"Received msg {msg!r}")
# #                     handle_msg(msg, addr[0], state)

# def send_msg(sock, msg):
#     # Prefix each message with a 4-byte length (network byte order)
#     msg = struct.pack('>I', len(msg)) + msg
#     sock.sendall(msg)

# def send_msg_of_kind(msg, kind, ips, s = socket.socket(socket.AF_INET, socket.SOCK_STREAM), connected = False):
#     own_ip = socket.gethostbyname(socket.gethostname())
#     ips = [ip for ip in ips if ip != own_ip]

#     if not s: s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: 
#     while not connected:
#         try:
#             s.connect((ips[0], 65432))
#             print(f"Established connection with {ips[0]}")
#             connected = True
#         except:
#             sleep(0.5)
#             connected = False 
#     print(f"Sending message of kind {kind} to {ips[0]}")
#     getch()
#     message = pickle.dumps((kind, msg, ips))
#     send_msg(s, message)
        
#     # print(f"\nSending message of kind {kind} with contents:\n\t{msg}\n to all of these: {ips}\n") 
#     # msg = pickle.dumps((kind, msg, ips))
#     # for ip in ips:
#     #     try:
#     #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     #         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     #             # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     #             s.connect((ip, 65432))
#     #             print(f"\nSending message of kind {kind} to {ip}\n") 
#     #             send_msg(s, msg)
#     #     except:
#     #         pass

# def recv_msg(sock):
#     # Read message length and unpack it into an integer
#     raw_msglen = recvall(sock, 4)
#     if not raw_msglen:
#         return None
#     msglen = struct.unpack('>I', raw_msglen)[0]
#     # Read the message data
#     return recvall(sock, msglen)

# def recvall(sock, n):
#     # Helper function to recv n bytes or return None if EOF is hit
#     data = bytearray()
#     while len(data) < n:
#         packet = sock.recv(n - len(data))
#         if not packet:
#             return None
#         data.extend(packet)
#     return data

# def listen(state):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.bind(('', 65432))
#         s.listen()
#         conn, addr = s.accept()
#         with conn:
#             print(f"Connected by {addr}")
#             while True:
#                 msg = recv_msg(conn)
#                 if not msg:
#                     break
#                 handle_msg(msg, addr, state)

# def request_ledger(ips):
#     send_msg_of_kind(b'0', "req_ledger", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (b'0', "req_ledger", ips)).start()

# def request_users(ips):
#     send_msg_of_kind(b'0', "req_users", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (b'0', "req_users", ips)).start()

# def send_users(msg, ips):
#     send_msg_of_kind(msg, "users", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (msg, "users", ips)).start()

# def send_ledger(msg, ips):
#     send_msg_of_kind(msg, "ledger", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (msg, "ledger", ips)).start()

# def send_transaction(msg, ips):
#     send_msg_of_kind(msg, "transaction", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (msg, "transaction", ips)).start()

# def send_ip(msg, ips):
#     send_msg_of_kind(msg, "ip", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (msg, "ip", ips)).start()

# # def send_mined_block(msg, ips, ledger_after):
# #     own_ip = socket.gethostbyname(socket.gethostname())
# #     ips = [ip for ip in ips if ip != own_ip]
# #     msg = pickle.dumps(("block", msg, ips, ledger_after))
# #     for ip in ips:
# #         try:
# #             socketer.connect((ip, 5005))
# #             send_msg(socketer, msg)
# #         except:
# #             pass

# def send_user(user, pub_key, ips):
#     user.public_key_on_user = pub_key
#     send_msg_of_kind(user, "user", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (user, "user", ips)).start()

# def send_rem_transaction(msg, ips):
#     send_msg_of_kind(msg, "transaction_rem", ips)
#     # threading.Thread( target = send_msg_of_kind
#     #                 , args = (msg, "transaction_rem", ips)).start()

# def start_listener(state):
#     threading.Thread(target = listen, args = (state,)).start()