"""Day schedule database."""

from uuid import uuid4
import redis_client
import control
import re
import parsedatetime
import time
import datetime
from twisted.internet import defer


class MatchDB(object):
    """A match database."""
    def __init__(self):
        """Default constructor."""
        pass

    def create_match(self, name, time, format = 'league'):
        """Schedule a match."""
        redis_client.connection.set('match:matches:{0}:format'.format(name),
                                    format)
        redis_client.connection.zadd('match:schedule', time, name)
        redis_client.connection.publish('match:schedule', 'update')

    def cancel_match(self, name):
        """Cancel an event in the day's schedule."""
        redis_client.connection.delete('match:matches:{0}:format'.format(name))
        redis_client.connection.zrem('match:schedule', name)
        redis_client.connection.publish('match:schedule', 'update')

    def set_teams(self, name, teams):
        """Set the teams for a match."""
        redis_client.connection.delete('match:matches:{0}:teams'.format(name))
        if teams is not None:
            redis_client.connection.rpush('match:matches:{0}:teams'.format(name),
                                          *teams)

    def matches_between(self, start, end):
        """Get events between a given start and end point, specified in
        seconds from the start of the day.

        Returns a Twisted Deferred on (name, time) pairs."""
        return redis_client.connection.zrangebyscore('match:schedule',
                                                     start,
                                                     end,
                                                     withscores=True)

matches = MatchDB()

class ParseError(Exception):
    """Indicates an error when parsing time values."""
    pass

def parse_time(s):
    """Parse a human-readable time format into a UNIX timestamp."""
    calendar = parsedatetime.Calendar()
    result, accuracy = calendar.parse(s)
    if accuracy == 0:
        raise ParseError()
    return time.mktime(result)

def format_time(n):
    """Convert from a UNIX timestamp into a human-readable time format."""
    return str(datetime.datetime.fromtimestamp(n))


@control.handler('add-match')
def perform_add_match(responder, options):
    matches.create_match(options['<name>'],
                         parse_time(options['<time>']),
                         'knockout' if options['--knockout'] else 'league')
    responder('Match {0} scheduled.'.format(options['<name>']))

@control.handler('del-match')
def perform_del_match(responder, options):
    matches.cancel_match(options['<name>'])
    responder('Match {0} canceled.'.format(options['<name>']))

@control.handler('set-match-teams')
def perform_set_match_teams(responder, options):
    matches.set_teams(options['<name>'],
                      options['<teams>'])
    responder('Teams set.')

@control.handler('clear-match-teams')
def perform_clear_match_teams(responder, options):
    matches.set_teams(options['<name>'], '')
    responder('Teams cleared.')

@control.handler('list-matches')
@defer.inlineCallbacks
def perform_list_matches(responder, options):
    fr = parse_time(options['<from>'])
    to = parse_time(options['<to>'])
    output = yield matches.matches_between(fr, to)
    if not output:
        responder('No matches.')
    else:
        for match, time in output:
            responder('{0}: {1}'.format(format_time(time), match))

