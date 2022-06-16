from dataclasses import dataclass
import datetime
import threading

@dataclass
class ServerState:
    # Static
    version: str
    host_ip: str
    host_port: int
    serv_name: str
    start_time: datetime.datetime = datetime.datetime.now() # UTC timezone
    max_connections: int = -1 # A value of -1 represents no limit
    # Dynamic
    is_running: threading.Event = threading.Event() # Synchronises thread shutdown
    n_current_connections: int = 0
    n_historic_connections: int = 0 # Number of (non-unique) connections made in total
