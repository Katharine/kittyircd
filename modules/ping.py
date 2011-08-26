from core.response_codes import *
import datetime
import eventlet

thread = None
def init():
    global thread
    add_hook('PING', received_ping)
    add_hook('PONG', received_pong)
    add_hook('incoming_message', received_something)
    add_hook('connection_init', connected)
    thread = eventlet.spawn(ping_all)

def shutdown():
    thread.kill()

def received_ping(connection, args):
    if len(args) == 0:
        connection.message(server.host, ERR_NOORIGIN, "No origin specified")
    else:
        connection.message(None, "PONG", args[0])

def connected(connection):
    connection.last_ping = datetime.datetime.now()

def received_pong(connection, args):
    if len(args) == 0:
        connection.message(server.host, ERR_NOORIGIN, "No origin specified")
    elif args[0] == server.host:
        connection.last_ping = datetime.datetime.now()

def received_something(connection, message):
    connection.last_ping = datetime.datetime.now()

def ping_all():
    while True:
        for user in m('user_manager').local_users().values():
            time_passed = datetime.datetime.now() - user.last_ping
            if time_passed > datetime.timedelta(minutes=7):
                # Bad luck.
                user.terminate("Ping timeout: %s" % time_passed)
            elif datetime.datetime.now() - user.last_ping > datetime.timedelta(minutes=5):
                user.message(None, "PING", server.host)
        eventlet.sleep(120)
