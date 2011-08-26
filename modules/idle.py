import datetime

def init():
    add_hook('connection_init', deidle)
    add_hook('PRIVMSG', deidle)

def deidle(connection, *args, **kwags):
    connection.last_active = datetime.datetime.now()
