from twisted.python import log
from twisted.internet import protocol, reactor, threads
from twisted.words.xish import domish
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber.xmlstream import IQ
 
from wokkel.xmppim import MessageProtocol, PresenceClientProtocol
from wokkel.xmppim import AvailablePresence

import xmpp_commands

class TranslateMessageProtocol(MessageProtocol):
    
    def __init__(self, jid):
        super(TranslateMessageProtocol, self).__init__()
        self.jid = jid.full()
        
    def connectionInitialized(self):
        super(TranslateMessageProtocol, self).connectionInitialized()
        log.msg("Connected!")

        self.send(AvailablePresence())
        
        self.commands=xmpp_commands.all_commands
        #self.commands={}
        #for c in commands:
            #self.commands[c] = commands[c]
            #for a in c.aliases:
                #self.commands[a] = c
        log.msg("Loaded commands: %s" % `sorted(self.commands.keys())`)
        
    def connectionLost(self, reason):
        log.msg('Disconnected!')
    
    def send_plain(self, jid, content):
        msg = domish.Element((None, "message"))
        msg["to"] = jid
        msg["from"] = self.jid
        msg["type"] = 'chat'
        msg.addElement("body", content=content)
 
        self.send(msg)
        
    def onError(self, msg):
        log.msg("Error received for %s: %s" % (msg['from'], msg.toXml()))
        
    def onMessage(self, msg):
        try:
            self.__onMessage(msg)
        except KeyError:
            log.err()
            
    def __onMessage(self, msg):
        if msg.getAttribute("type") == 'chat' \
            and hasattr(msg, "body") \
            and msg.body:
            a = unicode(msg.body).strip().split(None, 1)
            args = len(a) > 1 and a[1] or None
            self.__onUserMessage(a, args, msg)
            
    def __onUserMessage(self, a, args, msg):
        jid = msg['from']
        content = unicode(msg.body).strip()
        cmd = self.commands.get(a[0].lower())
        if cmd:
            cmd(jid, self, args)
        else:
            self.send_plain(msg['from'],"No such command %s\n" % str(a[0]))

        
    
        
