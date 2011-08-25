from core.response_codes import *
import config

class UserManager(object):
    """Manages users!"""
    def __init__(self):
        self.users = {}
        self.pending_users = []
        add_hook('connection_init', self.new_user)
        add_hook('connection_destroy', self.dead_user)
        add_hook('NICK', self.nick)
        add_hook('USER', self.user)
        add_hook('QUIT', self.quit)
        add_hook('MODE', self.mode)
        
    def shutdown(self):
        # We kill everyone now.
        logger.warn("Terminating all connections to avoid inconsistencies.")
        for user in self.pending_users:
            logger.info("Disconnecting unregistered user.")
            user.terminate("user_manager module unloading!")
        for user in self.users:
            logger.info("Disconnecting %s" % user)
            self.users[user].terminate("user_manager module unloading!")
    
    def dead_user(self, connection):
        if connection in self.pending_users:
            self.pending_users.remove(connection)
        else:
            if connection.nick.lower() in self.users:
                del self.users[connection.nick.lower()]
    
    def new_user(self, connection):
        connection.nick = None
        connection.user = None
        connection.modes = set()
        connection.real_name = None
        connection.registered = False
        self.pending_users.append(connection)
    
    def nick(self, connection, args):
        # Need to actually receive a nick
        if len(args) < 1:
            connection.message(server.host, ERR_NONICKNAMEGIVEN, "No nickname given")
        new_nick = args[0]
        nick_available = (new_nick.lower() not in self.users)
        if nick_available:
            for pending in self.pending_users:
                if pending.nick is not None and pending.nick.lower() == new_nick.lower():
                    nick_available = False
                    break
        
        if not nick_available:
            # Nick taken.
            connection.message(server.host, ERR_NICKNAMEINUSE, new_nick, "Nickname is already in use")
        else:
            connection.nick = new_nick
            if connection.registered:
                # Tell them their nick changed.
                connection.message("%s!%s@%s" % (connection.nick, connection.ident, connection.host), "NICK", new_nick)
                call_hook('nick_updated', connection, new_nick)
            else:
                self.process_registration(connection)
    
    def user(self, connection, args):
        if len(args) < 4:
            connection.message(server.host, ERR_NEEDMOREPARAMS, "Not enough parameters")
            return
        if connection.registered:
            connection.message(server.host, ERR_ALREADYREGISTERED, "Unauthorized command (already registered)")
            return
        user, mask, unused, realname = args
        try:
            mask = int(mask)
            if mask & 0x2:
                connection.modes.add('w')
            if mask & 0x4:
                connection.modes.add('i')
        except ValueError:
            pass
        connection.user = user
        connection.real_name = realname
        self.process_registration(connection)
    
    def quit(self, connection, args):
        if len(args) == 0:
            message = "Client disconnected from IRC"
        else:
            message = args[0]
        connection.terminate("Quit: %s" % message)
    
    def mode(self, connection, args):
        if len(args) < 2:
            connection.message(server.host, ERR_NEEDMOREPARAMS, "Not enough parameters")
            return
        if args[0][0] in ('#',):
            return
        if args[0].lower() != connection.nick.lower():
            connection.message(server.host, ERR_USERSDONTMATCH, "Cannot change mode for other users")
        modes = connection.modes
        old_modes = modes.copy()
        direction = 0
        for char in args[1]:
            if char == '+':
                direction = 1
            elif char == '-':
                direction = -1
            elif char in 'aiwroOs':
                if direction == 1:
                    modes.add(char)
                elif direction == -1:
                    modes.remove(char)
            else:
                connection.modes = old_modes
                connection.message(server.host, ERR_UMODEUNKNOWNFLAG, "Unknown MODE flag")
                return
        connection.message(server.host, RPL_UMODEIS, ''.join(modes))
        

    def process_registration(self, connection):
        if connection not in self.pending_users:
            return
        if connection.nick is None or connection.user is None:
            return
        self.users[connection.nick.lower()] = connection
        self.pending_users.remove(connection)
        self.welcome(connection)
        call_hook('registered_user', connection)
    
    def welcome(self, connection):
        connection.message(server.host, 1, "Welcome to the Internet Relay Network, %s!%s@%s" % (connection.nick, connection.user, connection.host))
        connection.message(server.host, 2, "Your host is %s, running version %s %s" % (server.host, config.SERVER_NAME, config.SERVER_VERSION))
        connection.message(server.host, 3, "This server was created %s" % server.startup.strftime('%a %b %d %Y at %H:%M:%S %Z UTC'))
        connection.message(server.host, 4, server.host, "%s%s" % (config.SERVER_NAME, config.SERVER_VERSION), 'iw', 'o')

manager = None

def local_users():
    return manager.users.values()

def init():
    global manager
    manager = UserManager()

def shutdown():
    manager.shutdown()
