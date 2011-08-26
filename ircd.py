#!/usr/bin/python
import eventlet
import eventlet.backdoor
import core.listener
import modules

def main(backdoor=True):
    # Open the back door, if we want it.
    if backdoor:
        eventlet.spawn(eventlet.backdoor.backdoor_server, eventlet.listen(('localhost', 6666)), {
            'load_module': lambda x: modules.load_module(x),
            'unload_module': lambda x: modules.unload_module(x),
            'm': lambda x: modules.get_module(x),
        })
    
    # Create our server.
    listener = core.listener.Listener()
    modules.set_server(listener)
    
    # Load modules as appropriate (manually for now)
    modules.load_module('user_manager')
    modules.load_module('motd')
    modules.load_module('ping')
    modules.load_module('whois')
    modules.load_module('idle')
    modules.load_module('privmsg')
    
    # Go go go!
    listener.run()

if __name__ == '__main__':
    main()
