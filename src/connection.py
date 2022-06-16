import socket
import threading
import uuid
import queue

from workers.receiver import Receiver
from workers.sender import Sender

def seq_int_gen():
    i = 0
    while True: 
        yield i
        i += 1
seq_int = seq_int_gen()

class Connection(threading.Thread):
    def __init__(self, server_state):
        super().__init__()

        # Connection properties
        self.is_active = False
        self.server_state = server_state

        # Client properties
        self.client_ip = None
        self.id = next(seq_int) # Public internal id (used for commands)
        self.uuid = uuid.uuid4() # Private interal id (used for auth)
        self.nick = None
        self.nick_time = None # Time at which nick was set 
        # When nicks collide, the younger nick must be replaced

        # Communication resources
        self.sent_from_client = queue.Queue() # Raw strings as recived from client; Enqueued by reciever
        self.send_to_client = queue.Queue() # Raw strings as to send to client; Dequeued by sender
        
        # The connection instance handles raw strings from the client by sorting them into the following queues (or consuming them personally, with a server_response enqueue)
        self.operator_commands = queue.Queue() # Commands like 'DIE' (shutdown server) or 'KICK'. Authed with server operator passcode
        self.standard_commands = queue.Queue() # Commands like 'INFO', 'NICK', or 'LIST'
        self.messages_from_client = queue.Queue() # Social messages, including info on intended recipients (this includes both general and private messages)

        # The connection instance handles messages to the client by consuming them from the following queues and making them into raw strings
        self.imperative_commands = queue.Queue() # Priority commands the client is intended to obey, such as 'KICK'. The client is not to be trusted
        self.server_responses = queue.Queue() # Informational messages which are named as if sent from the server, for 'INFO', 'MOTD', 'HELP', etc. commands 
        self.messages_to_client = queue.Queue() # Social messages for which the client is the intended recipient

        # Socket, passed to workers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.server_state.host_ip, self.server_state.host_port))
        self.client_conn = None # Connection object used by sender and receiver

        # Workers
        self.receiver = Receiver(self.sock, self.sent_from_client, self.is_active)
        self.sender = Sender(self.sock, self.send_to_client, self.is_active)

    def run(self):
        # Start receiver thread and await client connection through it
        self.receiver.start()
        self.receiver.has_client.wait()
        # We have found a client !
    
        self.is_active = True
        self.server_state.n_current_connections += 1
        self.server_state.n_historic_connections += 1

        # Fetch info; start sender
        self.client_conn, self.client_ip = self.receiver.client_conn, self.receiver.client_ip
        self.sender.start(self.client_conn)

        self.imperative_commands.enqueue({'type': 'IDGRANT', 'id':self.id, 'uuid':self.uuid})

        # Main behaviour loop
        while self.receiver.has_client.is_set() and self.server_state.is_running.is_set():
            self.handle_received()
            self.handle_sent()

        sock.close()
        self.server_state.n_current_connections -= 1


    def handle_received(self):
        while not self.sent_from_client.empty():

            """Examples
                Social messages:
            Hello world
            /msg 0 Hello world
            
                Standard commands:    
            /info
            /nick Name

                Operator commands:
            /kill
            /kick other
            """

            raw_message = self.sent_from_client.get()

            parted_message = raw_message.partition(" ") # Only over first space
            command = parted_message[0] if raw_message[0] == "/" else None
            parameter = parted_message[2] if command else raw_message

            match (command, parameter):
                case [None, contents]:
                    self.messages_from_client.enqueue({"type":"SOCMSG", 
                                                    "to":None,
                                                    "contents":parameter})
                case ["/nick", parameter]:
                    self.nick = parameter
                    self.nick_time = datetime.datetime.now()
                    self.standard_command.enqueue({"type":"NICK", 
                                                    "nick":parameter})
                case ["/info", parameter]: ## Consumes directly
                    self.server_response.enqueue({"type":"INFOREQ", 
                                                    "version":self.server_status.version,
                                                    "name":self.server_status.serv_name,
                                                    "start_time":str(self.server_status.start_time),
                                                    "current_connections":self.server_status.n_current_connections,
                                                    "historic_connections":self.server_status.n_historic_connections})


