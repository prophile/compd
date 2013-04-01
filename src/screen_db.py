"""Screen database."""

import redis_client
import control
import re
from twisted.internet import defer

class ScreenDB(object):
    """A screen database."""
    def __init__(self):
        """Default constructor."""
        pass

    def set_mode(self, screen, mode):
        redis_client.connection.set('screen:{0}:mode'.format(screen),
                                    mode)
        redis_client.connection.publish('screen:update', 'update')

    def set_override(self, screen, override):
        if override is not None:
            redis_client.connection.set('screen:{0}:override'.format(screen),
                                        override)
        else:
            redis_client.connection.delete('screen:{0}:override'.format(screen))
        redis_client.connection.publish('screen:update', 'update')

    @defer.inlineCallbacks
    def list(self):
        screens = yield redis_client.connection.keys('screen:*:mode')
        entries = {}
        for screen in screens:
            screenID = screen.split(':')[1]
            mode = yield redis_client.connection.get('screen:{0}:mode'.format(screenID))
            host = yield redis_client.connection.get('screen:{0}:host'.format(screenID))
            entries[screenID] = {'mode': mode,
                                 'host': host}
        defer.returnValue(entries)

screens = ScreenDB()

@control.handler('screen-list')
@defer.inlineCallbacks
def perform_screen_list(responder, options):
    screen_list = yield screens.list()
    for screen, settings in screen_list.iteritems():
        if settings['host'] is None:
            online_string = 'offline'
        else:
            online_string = 'online from {0} port {1}'.format(*settings['host'].split(' '))
        responder('{0} - {1} ({2})'.format(screen,
                                           settings['mode'],
                                           online_string))

@control.handler('screen-set-mode')
def perform_screen_set_mode(responder, options):
    screens.set_mode(options['<id>'], options['<mode>'])
    responder('Mode set.')

@control.handler('screen-override')
def perform_screen_override(responder, options):
    screens.set_override(options['<id>'], options['<message>'])
    responder('Override set.')

@control.handler('screen-clear-override')
def perform_screen_clear_override(responder, options):
    screens.set_override(options['<id>'], None)
    responder('Override cleared.')

