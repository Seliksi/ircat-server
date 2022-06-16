import utils
import connection 

def main():
    ss = utils.ServerState("0.0.1", "127.0.0.1", 6668, "cat")

    c = connection.Connection(ss)
    c.start()
