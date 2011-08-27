from core.response_codes import *

channels = {}

class Channel(object):
    def __init__(self, name):
        self.name = name
        self.topic = ''
        self.members = set()
        self.modes = ''
        self.member_modes = {}
        self.key = None
        self.limit = None
    
    def add(self, member, key=None):
        if self.limit is not None and len(self.members) >= self.limit:
            member.message(server.host, ERR_CHANISFULL, self.name, "Cannot join channel (+l)")
            return
        if self.key is not None and key != self.key:
            member.message(server.host, ERR_BADCHANNELKEY, self.name, "Cannot join channel (+k)")
            return
        self.members.add(member)
        member.channels.add(self)
        self.message(None, "%s!%s@%s" % (member.nick, member.user, member.host), "JOIN", self.name)
        if self.topic != '':
            member.message(server.host, RPL_TOPIC, self.name, self.topic)
        else:
            member.message(server.host, RPL_NOTOPIC, self.name, "No topic is set")
    
    def remove(self, member, reason=''):
        if member not in self.members:
            member.message(server.host, ERR_NOTONCHANNEL, self.name, "You're not on that channel")
            return
        self.message(None, "%s!%s@%s" % (member.nick, member.user, member.host), 'PART', self.name, reason)
        self.members.remove(member)
        member.channels.remove(self)
    
    def quit(self, member, reason=''):
        self.members.remove(member)
        self.message(member, member, 'QUIT', reason)
    
    def message(self, exclude, origin, message, *args):
        if exclude is None:
            exclude = set()
        if not hasattr('', '__iter__'): # Check if it's iterable. This will break under python 3.
            exclude = (exclude,)
        for user in self.members:
            if user not in exclude and user.nick not in exclude:
                user.message(origin, message, *args)
    
    def prefix(self, nick):
        mode = self.member_modes.get(nick.lower(), '')
        if 'o' in mode:
            return '@%s' % nick
        elif 'v' in mode:
            return '+%s' % nick
        return nick

def init():
    add_hook('connection_init', connection_init)
    add_hook('connection_destroy', connection_destroy)
    add_hook('JOIN', join)
    add_hook('NAMES', names)
    add_hook('PART', part)

def connection_init(connection):
    connection.channels = set()
    
def connection_destroy(connection):
    for channel in connection.channels:
        channel.quit(connection, connection.disconnect_reason)
    connection.channels.clear()

def join(origin, args):
    if len(args) < 1:
        origin.message(server.host, RPL_NEEDMOREPARAMS, "JOIN", "Need more parameters")
        return
    if args[0] == '0':
        # This is actually a request to part all.
        part(origin, [','.join(origin.channels)])
        return
    joining = args[0].split(',')
    if len(args) > 1:
        keys = args[1].split(',')
    else:
        keys = ['' for x in channels]
    i = 0
    for channel in joining:
        if channel.lower() not in channels:
            channels[channel.lower()] = Channel(channel)
        channels[channel.lower()].add(origin, keys[i] if len(keys) >= i+1 else None)
        names(origin, [channel])
        i += 1

def part(origin, args):
    if len(args) < 1:
        origin.message(server.host, RPL_NEEDMOREPARAMS, "JOIN", "Need more parameters")
        return
    parting = args[0].split(',')
    message = args[1] if len(args) > 1 else origin.nick
    for chan_name in parting:
        if chan_name.lower() not in channels:
            continue
        channel = channels[chan_name.lower()]
        channel.remove(origin, message)

def names(origin, args):
    if len(args) == 0:
        origin.message(server.host, RPL_ENDOFNAMES, "End of NAMES list")
        return
    chans = args[0].split(',')
    for channel in chans:
        if channel.lower() in channels:
            chan = channels[channel.lower()]
            names = [chan.prefix(x.nick) for x in chan.members]
            chan_prefix = '@' if 's' in chan.modes else '='
            while names:
                origin.message(server.host, RPL_NAMREPLY, "%s %s" % (chan_prefix, channel), ' '.join(names[0:30]))
                names = names[30:]
        origin.message(server.host, RPL_ENDOFNAMES, channel, "End of NAMES list")
    