from twisted.python import log
from twisted.internet import protocol, reactor, threads
from twisted.words.xish import domish
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber.xmlstream import IQ

from wokkel.xmppim import MessageProtocol, PresenceClientProtocol
from wokkel.xmppim import AvailablePresence

import xmpp_commands
import time

class TranslateMessageProtocol(MessageProtocol):

    def __init__(self, jid):
        super(TranslateMessageProtocol, self).__init__()
        self.jid = jid.full()

    def connectionInitialized(self):
        super(TranslateMessageProtocol, self).connectionInitialized()
        log.msg("Connected!")

        self.send(AvailablePresence())

        commands=xmpp_commands.all_commands
        self.commands={}
        for c in commands:
            self.commands[c] = commands[c]
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


class TranslatePresenceProtocol(PresenceClientProtocol):

    started = time.time()
    connected = None
    lost = None
    num_connections = 0

    def __init__(self, jid):
        super(TranslatePresenceProtocol, self).__init__()
        self.jid = jid.full()

    def connectionInitialized(self):
        super(TranslatePresenceProtocol, self).connectionInitialized()
        self.connected = time.time()
        self.lost = None
        self.num_connections += 1
        self.update_presence()


    def connectionLost(self, reason):
        self.connected = None
        self.lost = time.time()

    def presence_fallback(self, *stuff):
        log.msg("Running presence fallback.")
        self.available(None, None, {None: "Hi, everybody!"})

    def update_presence(self):
        status="Translating a lot"
        self.available(None, None, {None: status})

    def subscribedReceived(self, entity):
        log.msg("Subscribe received from %s" % (entity.userhost()))
        #welcome_message = 'Welcome.'
        #self.send_plain(entity.full(), welcome_message)

    def unsubscribedReceived(self, entity):
        log.msg("Unsubscribed received from %s" % (entity.userhost()))
        self.unsubscribe(entity)
        self.unsubscribed(entity)

    def subscribeReceived(self, entity):
        log.msg("Subscribe received from %s" % (entity.userhost()))
        self.subscribe(entity)
        self.subscribed(entity)
        self.update_presence()

    def unsubscribeReceived(self, entity):
        log.msg("Unsubscribe received from %s" % (entity.userhost()))
        self.unsubscribe(entity)
        self.unsubscribed(entity)
        self.update_presence()
