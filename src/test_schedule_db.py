import schedule_db
import mock
import redis_client
import control
from twisted.internet import defer

def test_new():
    uuid_handler = mock.Mock(return_value = 'eyes')
    fake_connection = mock.Mock()
    fake_connection.zadd = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('schedule_db.create_id', uuid_handler), \
         mock.patch('redis_client.connection', fake_connection):
        rv = schedule_db.schedule.create_event(100, 'lunch')
        assert rv == 'eyes'
        fake_connection.zadd.assert_called_once_with('comp:schedule',
                                             100, 'eyes')
        fake_connection.set.assert_called_once_with('comp:events:eyes',
                                            'lunch')
        fake_connection.zadd.reset_mock()
        fake_connection.set.reset_mock()
        # Test for invalid event types
        try:
            schedule_db.schedule.create_event(103, 'pony')
        except ValueError:
            # excellent, just make sure of things
            assert not fake_connection.zadd.called
            assert not fake_connection.set.called
        else:
            assert False

def test_cancel():
    fake_connection = mock.Mock()
    fake_connection.delete = mock.Mock()
    fake_connection.zrem = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        schedule_db.schedule.cancel_event('eyes')
        fake_connection.delete.assert_called_once_with('comp:events:eyes')
        fake_connection.zrem.assert_called_once_with('comp:schedule', 'eyes')

def test_events_between():
    # should be passthrough
    uniq1, uniq2, uniq3 = object(), object(), object()
    fake_connection = mock.Mock()
    fake_connection.zrangebyscore = mock.Mock(return_value = uniq1)
    with mock.patch('redis_client.connection', fake_connection):
        result = schedule_db.schedule.events_between(uniq2, uniq3)
        assert result is uniq1
        assert fake_connection.zrangebyscore.called_with('comp:schedule',
                                                         uniq2,
                                                         uniq3,
                                                         withscores=True)

def test_time_parse():
    assert schedule_db.parse_time('9:00') == 3600*9
    assert schedule_db.parse_time('12:00') == 3600*12
    assert schedule_db.parse_time('16:30') == 3600*16 + 60*30
    assert schedule_db.parse_time('16:30:35') == 3600*16 + 60*30 + 35
    try:
        schedule_db.parse_time('whenever')
        assert False
    except schedule_db.ParseError:
        pass

def test_format_time():
    assert schedule_db.format_time(3600*8 +
                                   60*3 +
                                   45) == '8:03:45'

def test_command_unschedule():
    mock_cancel = mock.Mock()
    with mock.patch('schedule_db.schedule.cancel_event', mock_cancel):
        control.handle('unschedule eyes')
    mock_cancel.assert_called_once_with('eyes')

def test_command_schedule():
    responder = mock.Mock()
    create_event = mock.Mock(return_value = 'eyes')
    with mock.patch('schedule_db.schedule.create_event', create_event):
        control.handle('schedule lunch moo', responder)
        responder.assert_called_once_with("Sorry, I didn't understand that time")
        responder.reset_mock()
        control.handle('schedule lunch 12:00', responder)
        responder.assert_called_once_with("Scheduled as eyes")
        create_event.assert_called_once_with(12*3600, 'lunch')

def test_command_show_schedule():
    responder = mock.Mock()
    df = defer.Deferred()
    events_between = mock.Mock(return_value = df)
    with mock.patch('schedule_db.schedule.events_between', events_between):
        control.handle('show-schedule moo 12:00', responder)
        responder.assert_called_once_with("Sorry, I didn't understand that time")
        responder.reset_mock()
        control.handle('show-schedule 9:00 13:00', responder)
        events_between.assert_called_once_with(9*3600, 13*3600)
        df.callback([('eyes', 10*3600)])
        responder.assert_called_once_with('10:00:00 - eyes')
        responder.reset_mock()
    df = defer.Deferred()
    events_between = mock.Mock(return_value = df)
    with mock.patch('schedule_db.schedule.events_between', events_between):
        control.handle('show-schedule 9:00 13:00', responder)
        events_between.assert_called_once_with(9*3600, 13*3600)
        df.callback([])
        responder.assert_called_once_with('No events in that time period')


