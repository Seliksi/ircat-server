import threading

class Worker(threading.Thread):
    def __init__(self, sock, queue, i_should_run):
        super().__init__()
        self.sock = sock
        self.queue = queue
        self.i_should_run = i_should_run
