import eventlet
from eventlet.green import socket
import core.connection
import datetime

class Listener(object):
    """Listens on a relevant port."""
    def __init__(self, port=6667, listen='0.0.0.0'):
        self.port = port
        self.listen = listen
        self.host = socket.getfqdn(listen)
        self.startup = datetime.datetime.utcnow()
    
    def connection(self, socket):
        print "Client connected."
        user = core.connection.Connection(self, socket)
        user.loop()
        print "Client disconnected."
    
    
    def run(self):
        pool = eventlet.GreenPool(1000)
        server = eventlet.listen((self.listen, self.port))
        while True:
            sock, address = server.accept()
            pool.spawn_n(self.connection, sock)
