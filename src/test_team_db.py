import team_db
import mock
import redis_client
import control
from twisted.internet import defer

def test_add():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        team_db.roster.add('aaa',
                           college = 'St. Pony College',
                           name = 'Team Pony')
        fake_connection.set.assert_has_calls([mock.call('team:aaa:college',
                                                        'St. Pony College'),
                                              mock.call('team:aaa:name',
                                                        'Team Pony'),
                                              mock.call('team:aaa:notes',
                                                        ''),
                                              mock.call('team:aaa:present',
                                                        'no')],
                                             any_order = True)

def test_delete():
    fake_connection = mock.Mock()
    fake_connection.delete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        team_db.roster.delete('aaa')
        fake_connection.delete.assert_has_calls([mock.call('team:aaa:college'),
                                                 mock.call('team:aaa:name'),
                                                 mock.call('team:aaa:notes'),
                                                 mock.call('team:aaa:present')],
                                                any_order = True)

def test_mark_present():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        team_db.roster.mark_present('aaa')
        fake_connection.set.assert_called_once_with('team:aaa:present',
                                                    'yes')
def test_mark_absent():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        team_db.roster.mark_absent('aaa')
        fake_connection.set.assert_called_once_with('team:aaa:present',
                                                    'no')

def test_update():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        team_db.roster.update('aaa',
                              college = 'St. Eyes College',
                              name = 'Pony Gravity',
                              notes = 'free form text')
        fake_connection.set.assert_has_calls([mock.call('team:aaa:college',
                                                        'St. Eyes College'),
                                              mock.call('team:aaa:name',
                                                        'Pony Gravity'),
                                              mock.call('team:aaa:notes',
                                                        'free form text')],
                                             any_order = True)


