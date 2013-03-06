import txredisapi as redis
from twisted.internet import defer, reactor
import config

connection = None

def run_redis_client(on_started):
    df = redis.makeConnection(config.redis['host'],
                              config.redis['port'],
                              config.redis['db'],
                              poolsize = 8,
                              reconnect = True,
                              isLazy = False)
    def done(pony):
        global connection
        connection = pony
        on_started()
    df.addCallback(done)

