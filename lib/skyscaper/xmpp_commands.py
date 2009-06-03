from twisted.python import log
from twisted.words.xish import domish
from twisted.words.protocols.jabber.jid import JID
from twisted.web import client
from twisted.internet import reactor, threads, defer
from wokkel import ping

from translate import Translate
from languages import Language
import protocol

all_commands = {}

def arg_required(validator=lambda n: n):
    def f(orig):
        def every(self, jid, prot, args):
            if validator(args):
                orig(self, jid, prot, args)
            else:
                prot.send_plain(jid, "Arguments required for %s:\n%s"
                    % (self.name, self.extended_help))
        return every
    return f
    
class BaseCommand(object):
    """Base class for command processors."""
 
    def __get_extended_help(self):
        if self.__extended_help:
            return self.__extended_help
        else:
            return self.help
 
    def __set_extended_help(self, v):
        self.__extended_help=v
 
    extended_help=property(__get_extended_help, __set_extended_help)
 
    def __init__(self, name, help=None, extended_help=None, aliases=[]):
        self.name=name
        self.help=help
        self.aliases=aliases
        self.extended_help=extended_help
 
    def __call__(self, user, prot, args, session):
        raise NotImplementedError()
 
    def is_a_url(self, u):
        try:
            parsed = urlparse.urlparse(str(u))
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except:
            return False
            
class TranslateCommand(BaseCommand):
    
    def __init__(self):
        super(TranslateCommand, self).__init__('translate', 
              'Perform a translation from one language to other languages')
    
    def _success(self, t_text, jid, prot, ld):
        prot.send_plain(jid, str(ld) + ': ' + t_text)
    
    def _error(self, e, jid, prot):
        prot.send_plain(jid, e)
    
    def _translate_in_all_languages(self, language_o, words):
        for language in Language.list_all_languages().split('\n'):
            try:
                t = Translate(Language(language_o.upper()), Language(language))
                t.translate(words.encode('utf-8')).addCallback(self._success, jid, prot, language) \
                                                  .addErrback(self._error, jid, prot) 
            except Exception:
                pass
        
    @arg_required()
    def __call__(self, jid, prot, args):
        language_o, raw = args.split(' ', 1)
        words, languages = raw.split(' -> ')
        languages = [ lan.strip() for lan in languages.split(',') ]
        for language in languages:
            try:
                t = Translate(Language(language_o.upper()), Language(language.upper()))
                t.translate(words.encode('utf-8')).addCallback(self._success, jid, prot, language.lower()) \
                                                  .addErrback(self._error, jid, prot)
            except Exception, e:
                self._error(e.message, jid, prot)

for __t in (t for t in globals().values() if isinstance(type, type(t))):
    if BaseCommand in __t.__mro__:
        try:
            i = __t()
            all_commands[i.name] = i
        except TypeError, e:
            log.msg("Error loading %s: %s" % (__t.__name__, str(e)))
            pass
