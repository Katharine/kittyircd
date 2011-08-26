from core.response_codes import *
import datetime

__depends__ = ['user_manager', 'idle']

def init():
    add_hook('ISON', ison)
    add_hook('USERHOST', userhost)
    add_hook('WHOIS', whois)
    add_hook('ADMIN', admin)
    add_hook('LUSERS', lusers)

def ison(connection, nicks):
    users = set([x.lower() for x in m('user_manager').net_users()])
    reply = []
    for nick in nicks:
        if nick.lower() in users:
            reply.append(nick)
    connection.message(server.host, RPL_ISON, ' '.join(reply))

def userhost(connection, hosts):
    hosts = hosts[:5]
    reply = []
    users = m('user_manager').net_users()
    for host in hosts:
        if host.lower() not in users:
            continue
        user = users[host.lower()]
        entry = "%s=+%s@%s" % (user.nick, user.user, user.host)
        reply.append(entry)
    connection.message(server.host, RPL_USERHOST, ' '.join(reply))

def admin(connection, args):
    connection.message(server.host, ERR_NOADMININFO, "No administrative info available.")

def lusers(connection, args):
    connection.message(server.host, RPL_LUSERCLIENT, "There are %s users and 0 services on 1 servers" % len(m('user_manger').net_users()))
    connection.message(server.host, RPL_LUSEROP, 0, "operator(s) online")
    connection.message(server.host, RPL_LUSERUNKNOWN, 0, "unknown connection(s)")
    connection.message(server.host, RPL_LUSERCHANNELS, 0, "channels formed")
    connection.message(server.host, RPL_LUSERME, "I have %s clients and 0 servers" % len(m('user_manager').local_users()))

def whois(connection, args):
    if len(args) == 0:
        connection.message(server.host, ERR_NONICKNAMEGIVEN, "No nickname given")
    elif len(args) == 2 and args[0].lower() != server.host.lower() and args[0] != args[1]: # This last check is dumb.
        connection.message(server.host, ERR_NOSUCHSERVER, args[0], "No such server")
    else:
        nick = args[0] if len(args) == 1 else args[1]
        if m('user_manager').user_exists(nick):
            user = m('user_manager').get_user(nick)
            connection.message(server.host, RPL_WHOISUSER, user.nick, user.user, user.host, '*', user.real_name)
            connection.message(server.host, RPL_WHOISSERVER, user.nick, user.server.host, 'N/A')
            if user.last_active:
                connection.message(server.host, RPL_WHOISIDLE, user.nick, (datetime.datetime.now() - user.last_active).total_seconds(), "seconds idle")
            connection.message(server.host, RPL_ENDOFWHOIS, user.nick, "End of WHOIS list")
        else:
            connection.message(server.host, ERR_NOSUCHNICK, nick, "No such nick/channel")
