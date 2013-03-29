from twisted.internet import reactor, protocol

import sys
import config

class RedisDataReceiver(protocol.ProcessProtocol):
    def __init__(self, on_started):
        self.on_started = on_started

    def outReceived(self, data):
        print >>sys.stderr, data,
        if 'now ready to accept connections' in data:
            self.on_started()

    def errReceived(self, data):
        print >>sys.stderr, data,

def run_redis_server(on_started):
    print >>sys.stderr, "Starting Redis server..."
    server = config.redis['server']
    reactor.spawnProcess(RedisDataReceiver(on_started),
                         server,
                         args = [server, 'redis.conf'],
                         path = '../database/')

