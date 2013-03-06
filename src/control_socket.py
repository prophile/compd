from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
import config
import control

class ControlHandler(LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        self.sendLine("Hello!")

    def lineReceived(self, line):
        print "Got line: {0}".format(line)
        control.handle(line, self.sendLine)

class ControlHandlerFactory(Factory):
    protocol = ControlHandler

# TODO: make this listen on localhost only
def install_control_handler():
    endpoint = TCP4ServerEndpoint(reactor, config.control_port)
    endpoint.listen(ControlHandlerFactory())

