from uuid import uuid4
import redis_client
import control
import re


EVENT_TYPES = ('league', 'knockout', 'lunch', 'open',
               'tinker', 'photo', 'prizes', 'briefing')

def uuid(prefix):
    return '{0}-{1}'.format(prefix, str(uuid4())[:13])

class ScheduleDB(object):
    def __init__(self):
        pass

    def create_event(self, time, type_):
        if type_ not in EVENT_TYPES:
            raise ValueError('unknown event type')
        id_ = uuid(type_)
        redis_client.connection.set('comp:events:{0}'.format(id_),
                                    type_)
        redis_client.connection.zadd("comp:schedule", time, id_)
        return id_

    def cancel_event(self, id_):
        redis_client.connection.delete('comp:events:{0}'.format(id_))
        redis_client.connection.zrem('comp:schedule', id_)

    def events_between(self, start, end):
        return redis_client.connection.zrangebyscore('comp:schedule',
                                                     start,
                                                     end,
                                                     withscores=True)

schedule = ScheduleDB()

class ParseError(Exception):
    pass

def parse_time(s):
    match = re.match('(\d+):(\d+)(?::(\d+))?', s)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3) or 0)
        return 3600*hours + 60*minutes + seconds
    else:
        raise ParseError()

def format_time(n):
    seconds = n % 60
    minutes = n // 60
    hours = minutes // 60
    minutes %= 60
    return '{0}:{1:02}:{2:02}'.format(hours, minutes, seconds)

@control.handler('schedule')
def perform_schedule(responder, options):
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
    id_ = options['<id>']
    schedule.cancel_event(id_)
    responder('Done!')

@control.handler('show-schedule')
def perform_show_schedule(responder, options):
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

