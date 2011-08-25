from core.response_codes import *
import config

def init():
    add_hook('registered_user', get_motd)
    add_hook('MOTD', get_motd)

def get_motd(connection, args=None):
    try:
        with open(config.motd_file) as f:
            connection.message(server.host, RPL_MOTDSTART, "- %s Message of the day -" % server.host)
            while True:
                line = f.readline()
                if not line:
                    break
                connection.message(server.host, RPL_MOTD, "- %s" % line.rstrip())
            connection.message(server.host, RPL_ENDOFMOTD, "- End of MOTD command")
    except:
        connection.message(server.host, ERR_NOMOTD, "MOTD File is missing")
