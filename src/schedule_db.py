"""Day schedule database."""

from uuid import uuid4
import redis_client
import control
import re
import parsedatetime
import time
import datetime


EVENT_TYPES = ('league', 'knockout', 'lunch', 'open',
               'tinker', 'photo', 'prizes', 'briefing')

def create_id(prefix):
    """Create a unique event ID. The prefix should specify the type of
    event, one of EVENT_TYPES."""
    return '{0}-{1}'.format(prefix, str(uuid4())[:13])

class ScheduleDB(object):
    """A schedule database."""
    def __init__(self):
        """Default constructor."""
        pass

    def create_event(self, time, type_):
        """Schedule an event in the day. time should be given as a second
        offset from the start of the day, and type_ should be one of
        EVENT_TYPES.

        Returns the ID of the event."""
        if type_ not in EVENT_TYPES:
            raise ValueError('unknown event type')
        id_ = create_id(type_)
        redis_client.connection.set('comp:events:{0}'.format(id_),
                                    type_)
        redis_client.connection.zadd("comp:schedule", time, id_)
        redis_client.connection.publish('comp:schedule', 'update')
        return id_

    def cancel_event(self, id_):
        """Cancel an event in the day's schedule."""
        redis_client.connection.delete('comp:events:{0}'.format(id_))
        redis_client.connection.zrem('comp:schedule', id_)
        redis_client.connection.publish('comp:schedule', 'update')

    def events_between(self, start, end):
        """Get events between a given start and end point, specified in
        seconds from the start of the day.

        Returns a Twisted Deferred on (id, time) pairs."""
        return redis_client.connection.zrangebyscore('comp:schedule',
                                                     start,
                                                     end,
                                                     withscores=True)

schedule = ScheduleDB()

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

@control.handler('schedule')
def perform_schedule(responder, options):
    """Handle the `schedule` command."""
    try:
        time = parse_time(options['<time>'])
    except ParseError:
        responder('Sorry, I didn\'t understand that time')
        return
    for type_ in EVENT_TYPES:
        if options[type_]:
            id_ = schedule.create_event(time, type_)
            responder('Scheduled as {0}'.format(id_))
            break
    else:
        responder('Not sure what event type that is?')

@control.handler('unschedule')
def perform_unschedule(responder, options):
    """Handle the `unschedule` command."""
    id_ = options['<id>']
    schedule.cancel_event(id_)
    responder('Done!')

@control.handler('show-schedule')
def perform_show_schedule(responder, options):
    """Handle the `show-schedule` command."""
    try:
        from_ = parse_time(options['<from>'])
        to_ = parse_time(options['<to>'])
    except ParseError:
        responder('Sorry, I didn\'t understand that time')
        return
    def onCompleted(entries):
        for k, v in entries:
            responder('{0} - {1}'.format(format_time(v), k))
        if not entries:
            responder('No events in that time period')
    schedule.events_between(from_, to_).addCallback(onCompleted)

