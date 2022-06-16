from workers.worker import Worker

class Sender(Worker):
    def run(self, conn):
        while self.i_should_run.is_set():
            message = self.queue.get(blocking=True)
            conn.send()
