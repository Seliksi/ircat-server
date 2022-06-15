import threading
import datetime

@dataclass
class ServerState:
    # Static
    self.version: str
    self.host_ip: str
    self.host_port: int
    self.serv_name: str
    self.start_time: datetime.datetime # UTC timezone
    self.max_connections: int # A value of -1 represents no limit
    # Dynamic
    self.is_running: threading.Event # Synchronises thread shutdown
    self.n_current_connections: int
    self.n_historic_connections: int # Number of (non-unique) connections made in total
