from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import config
import control
import re

class IRCBot(irc.IRCClient):
    def __init__(self, nick, user, gecos, channel, key = None):
        self.nickname = nick
        self.realname = gecos
        self.username = user
        self.channel = channel
        self.key = key
        self.lineRate = 0.35

    def signedOn(self):
        self.join(self.channel, self.key)
        control.subscribe(self.broadcast_info)

    def broadcast_info(self, message):
        self.say(self.channel, message)

    def privmsg(self, user, channel, msg):
        if channel != self.channel:
            return
        prefix = '{0}:'.format(self.nickname)
        if not msg.startswith(prefix):
            return
        content = msg[len(prefix):]
        sender = re.match('(.*)!(.*)@(.*)', user).group(1)
        def responder(response):
            self.say(channel, '{0}: {1}'.format(sender, response))
        control.handle(content, responder, short_fail = True)

class IRCBotFactory(protocol.ClientFactory):
    def __init__(self, configuration):
        self.configuration = configuration

    def buildProtocol(self, addr):
        return IRCBot(self.configuration['nick'],
                      self.configuration['user'],
                      self.configuration['gecos'],
                      self.configuration['channel'],
                      self.configuration['key'])

def install_irc_handler():
    configuration = config.irc
    if not configuration['enable']:
        return
    factory = IRCBotFactory(configuration)
    reactor.connectTCP(configuration['server'],
                       configuration['port'],
                       factory)

