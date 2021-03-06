import sys
sys.path.insert(0, "lib/twisted-googletranslate/lib")
sys.path.insert(0, "lib/skyscaper")
sys.path.insert(0, "lib/wokkel")
sys.path.insert(0, "lib")

from twisted.application import service
from twisted.words.protocols.jabber import jid
from wokkel.client import XMPPClient

from protocol import TranslateMessageProtocol, TranslatePresenceProtocol

application = service.Application("translate")

j = jid.internJID("yourjid")

xmppclient = XMPPClient(j, "password")
xmppclient.logTraffic = False
protocols = [TranslateMessageProtocol,
             TranslatePresenceProtocol]

for p in protocols:
    handler=p(j)
    handler.setHandlerParent(xmppclient)

xmppclient.setServiceParent(application)
