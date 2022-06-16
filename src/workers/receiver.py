import threading
from workers.worker import Worker

class Receiver(Worker):
    def __init__(self, sock, out_queue, i_should_run):
        super().__init__(sock, out_queue, i_should_run)

        self.has_client = threading.Event()
        self.conn = None
        self.client_ip = None

    def run(self):

        self.sock.listen()
        self.conn, self.client_ip = self.sock.accept()
        self.has_client.set() # Frees parent connection instance
        print(f"connection from {self.client_ip} made")
        while self.i_should_run.is_set():
            message = self.conn.recv(2**12)
            # TODO: make sure the whole message was contained in that
            self.queue.enqueue(message)

