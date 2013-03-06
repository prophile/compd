import txredisapi as redis
from twisted.internet import defer, reactor
import config

connection = None

@defer.inlineCallbacks
def run_redis_client(on_started):
    pony = yield redis.makeConnection(config.redis['host'],
                                      config.redis['port'],
                                      config.redis['db'],
                                      poolsize = 8,
                                      reconnect = True,
                                      isLazy = True)
    global connection
    connection = pony
    on_started()

