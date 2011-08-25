import modules
from core.response_codes import ERR_UNKNOWNCOMMAND
from eventlet.green import socket

class Connection(object):
    def __init__(self, sock):
        self.socket = sock
        self.fd = sock.makefile('rw')
        self.nick = None
        self.host, self.port = sock.getpeername()
        modules.call_hook('connection_init', self)
    
    def handle(self, line):
        origin = None
        line = line.strip("\r\n")
        modules.call_hook('incoming_message', self, line)
        if line[0] == ':':
            hostmask, line = line[1:].split(' ', 1)
            parts = hostmask.split('!', 1)
            origin = User(nick=parts[0])
            if len(parts) > 1:
                origin.ident, origin.hostname = parts[1].split('@', 1)

        parts = line.split(' :', 1)
        args = parts[0].split(' ')
        if len(parts) > 1:
            args.append(parts[1])

        command = args.pop(0).upper()
        if not modules.call_hook(command, self, args):
            # Send back an unsupported command error - nothing happened
            # Hack: we shouldn't have to pull server out of modules...
            self.message(modules.server.host, ERR_UNKNOWNCOMMAND, command, "Unknown command")
    
    def message(self, origin, command, *args):
        line_parts = []
        args = list(args)
        if origin is not None:
            line_parts.append(":%s" % origin)
        if isinstance(command, int):
            line_parts.append(str(command).rjust(3, '0'))
            line_parts.append(self.nick)
        else:
            line_parts.append(command)
        if len(args) > 0:
            last_arg = None
            if ' ' in args[-1]:
                last_arg = args.pop()
            line_parts.extend(args)
            if last_arg is not None:
                line_parts.append(':%s' % last_arg)
        line = ' '.join(line_parts)
        print "-> %s" % line
        self.fd.write("%s\r\n" % line)
        self.fd.flush()
    
    def terminate(self, reason=None):
        self.disconnect_reason = reason
        self.message(None, "ERROR", "Quit: %s" % reason)
        self.fd.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.connected = False
    
    def loop(self):
        self.connected = True
        while self.connected:
            line = self.fd.readline()
            if not line:
                print "User %s (%s) disconnected." % (self.nick, self.host)
                break
            print "<- %s" % line.rstrip()
            self.handle(line)
        modules.call_hook('connection_destroy', self)
