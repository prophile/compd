import scores_db
import mock
import redis_client
import control
from twisted.internet import defer
import yaml

# Unit tests

## ScoresDB access

def test_set_scores():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        scores_db.scores.set_match_score(1, 'ABC', 12)
        fake_connection.set.assert_called_once_with('comp:scores:1:ABC:game', 12)

def test_set_league_points():
    fake_connection = mock.Mock()
    fake_connection.mset = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        raw_data = {'ABC':1.0, 'DEF':2.0}
        scores_db.scores.set_league_points(1, raw_data)
        call_data = {'comp:scores:1:ABC:league':1.0, 'comp:scores:1:DEF:league':2.0}
        fake_connection.mset.assert_called_once_with(call_data)

def test_set_league_points():
    fake_connection = mock.Mock()
    fake_connection.mset = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        raw_data = {'ABC':1.0, 'DEF':2.0}
        scores_db.scores.set_league_points(1, raw_data)
        call_data = {'comp:scores:1:ABC:league':1.0, 'comp:scores:1:DEF:league':2.0}
        fake_connection.mset.assert_called_once_with(call_data)

def test_get_league_points():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    keys = ['comp:scores:1:ABC:league', 'comp:scores:2:ABC:league']
    fake_keys.callback(keys)
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    fake_points = defer.Deferred()
    fake_points.callback([2.0, 3.0])
    fake_connection.mget = mock.Mock(return_value = fake_points)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        points = scores_db.scores.get_league_points('ABC')
        # Assert that the right things were called
        fake_connection.keys.assert_called_once_with('comp:scores:*:ABC:league')
        fake_connection.mget.assert_called_once_with(*keys)

        # Check that the right result was output
        points.addCallback(did_complete)
        did_complete.assert_called_once_with(5.0)

def test_get_league_points_empty():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    fake_keys.callback([])
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    fake_points = defer.Deferred()
    fake_points.callback([])
    fake_connection.mget = mock.Mock(return_value = fake_points)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        points = scores_db.scores.get_league_points('ABC')
        # Assert that the right things were called (or not)
        fake_connection.keys.assert_called_once_with('comp:scores:*:ABC:league')
        assert not fake_connection.mget.called, "Should not call mget when no matches"

        # Check that the right result was output
        points.addCallback(did_complete)
        did_complete.assert_called_once_with(None)

def test_disqualify():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        scores_db.scores.disqualify(1, 'ABC')
        # Assert that the right things were called
        fake_connection.set.assert_called_once_with('comp:scores:1:ABC:dsq', True)

def test_re_qualify():
    fake_connection = mock.Mock()
    fake_connection.delete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        scores_db.scores.re_qualify(1, 'ABC')
        # Assert that the right things were called
        fake_connection.delete.assert_called_once_with('comp:scores:1:ABC:dsq')

def test_teams_in_match():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    fake_keys.callback(['comp:scores:1:ABC:game', 'comp:scores:1:DEF:game'])
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.teams_in_match(1)

        # Assert that the right things were called
        fake_connection.keys.assert_called_once_with('comp:scores:1:*:game')

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with(['ABC', 'DEF'])

def test_teams_in_match_empty():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    fake_keys.callback([])
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.teams_in_match(1)

        # Assert that the right things were called
        fake_connection.keys.assert_called_once_with('comp:scores:1:*:game')

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with([])

def test_teams_disqualified_in_match():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    fake_keys.callback(['comp:scores:1:ABC:dsq', 'comp:scores:1:DEF:dsq'])
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.teams_disqualified_in_match(1)

        # Assert that the right things were called
        fake_connection.keys.assert_called_once_with('comp:scores:1:*:dsq')

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with(['ABC', 'DEF'])

def test_teams_disqualified_in_match_empty():
    fake_connection = mock.Mock()
    fake_keys = defer.Deferred()
    fake_keys.callback([])
    fake_connection.keys = mock.Mock(return_value = fake_keys)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.teams_disqualified_in_match(1)

        # Assert that the right things were called
        fake_connection.keys.assert_called_once_with('comp:scores:1:*:dsq')

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with([])

def test_get_match_score():
    fake_connection = mock.Mock()
    fake_score = defer.Deferred()
    fake_score.callback(2)
    fake_connection.get = mock.Mock(return_value = fake_score)
    did_complete = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.get_match_score(1, 'ABC')

        # Assert that the right things were called
        fake_connection.get.assert_called_once_with('comp:scores:1:ABC:game')

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with(2)

def test_get_match_scores():
    fake_connection = mock.Mock()
    fake_teams = defer.Deferred()
    fake_teams.callback(['ABC', 'DEF'])
    fake_get_teams = mock.Mock(return_value = fake_teams)
    fake_score = defer.Deferred()
    fake_score.callback([2,3])
    fake_connection.mget = mock.Mock(return_value = fake_score)
    did_complete = mock.Mock()
    with mock.patch('scores_db.scores.teams_in_match', fake_get_teams), \
         mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.get_match_scores(1)

        # Assert that the right things were called
        fake_get_teams.assert_called_once_with(1)
        fake_connection.mget.assert_called_once_with(*['comp:scores:1:ABC:game',
                                                       'comp:scores:1:DEF:game'])

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with({'ABC':2, 'DEF':3})

def test_get_match_scores_empty():
    fake_connection = mock.Mock()
    fake_teams = defer.Deferred()
    fake_teams.callback([])
    fake_get_teams = mock.Mock(return_value = fake_teams)
    fake_score = defer.Deferred()
    fake_score.callback([2,3])
    fake_connection.mget = mock.Mock(return_value = fake_score)
    did_complete = mock.Mock()
    with mock.patch('scores_db.scores.teams_in_match', fake_get_teams), \
         mock.patch('redis_client.connection', fake_connection):
        # Get the value
        info = scores_db.scores.get_match_scores(1)

        # Assert that the right things were called
        fake_get_teams.assert_called_once_with(1)
        assert not fake_connection.mget.called, "Should not query scores we don't have"

        # Check that the right result was output
        info.addCallback(did_complete)
        did_complete.assert_called_once_with(None)

## Commands

def test_perform_set_score():
    fake_set_score = mock.Mock()
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.set_match_score', fake_set_score):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC',
                    '<score>': 3 }

        # Run the command
        scores_db.perform_set_score(fake_responder, options)

        # Assert that the right things were called
        fake_set_score.assert_called_once_with(1, 'ABC', 3)

        # Check that the right text was output
        fake_responder.assert_called_once_with('Scored 3 points for ABC in match 1')

def test_perform_get_score():
    fake_score = defer.Deferred()
    fake_score.callback(3)
    fake_get_score = mock.Mock(return_value = fake_score)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_score', fake_get_score):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC' }

        # Run the command
        scores_db.perform_get_score(fake_responder, options)

        # Assert that the right things were called
        fake_get_score.assert_called_once_with(1, 'ABC')

        # Check that the right text was output
        fake_responder.assert_called_once_with('Team ABC scored 3 in match 1')

def test_perform_get_score_yaml():
    fake_score = defer.Deferred()
    fake_score.callback(3)
    fake_get_score = mock.Mock(return_value = fake_score)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_score', fake_get_score):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC',
                    '--yaml': True }

        # Run the command
        scores_db.perform_get_score(fake_responder, options)

        # Assert that the right things were called
        fake_get_score.assert_called_once_with(1, 'ABC')

        # Check that the right text was output
        fake_responder.assert_called_once_with(yaml.dump({'score':3}))

def test_perform_get_scores():
    fake_scores = defer.Deferred()
    results = {'ABC':1, 'DEF':4}
    fake_scores.callback(results)
    fake_get_scores = mock.Mock(return_value = fake_scores)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_scores', fake_get_scores):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC' }

        # Run the command
        scores_db.perform_get_scores(fake_responder, options)

        # Assert that the right things were called
        fake_get_scores.assert_called_once_with(1)

        # Check that the right text was output
        fake_responder.assert_has_calls([mock.call('Team ABC scored 1 in match 1'),
                                         mock.call('Team DEF scored 4 in match 1')],
                                        any_order = True)

def test_perform_get_scores_empty():
    fake_scores = defer.Deferred()
    results = None
    fake_scores.callback(results)
    fake_get_scores = mock.Mock(return_value = fake_scores)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_scores', fake_get_scores):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC' }

        # Run the command
        scores_db.perform_get_scores(fake_responder, options)

        # Assert that the right things were called
        fake_get_scores.assert_called_once_with(1)

        # Check that the right text was output
        fake_responder.assert_called_once('No scores available for match 1')

def test_perform_get_scores_yaml():
    fake_scores = defer.Deferred()
    results = {'ABC':1, 'DEF':4}
    fake_scores.callback(results)
    fake_get_scores = mock.Mock(return_value = fake_scores)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_scores', fake_get_scores):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC',
                    '--yaml': True }

        # Run the command
        scores_db.perform_get_scores(fake_responder, options)

        # Assert that the right things were called
        fake_get_scores.assert_called_once_with(1)

        # Check that the right text was output
        fake_responder.assert_called_once_with(yaml.dump({'scores':results}))

def test_perform_get_scores_empty_yaml():
    fake_scores = defer.Deferred()
    results = None
    fake_scores.callback(results)
    fake_get_scores = mock.Mock(return_value = fake_scores)
    fake_responder = mock.Mock()
    with mock.patch('scores_db.scores.get_match_scores', fake_get_scores):

        options = { '<match-id>': 1,
                    '<tla>': 'ABC',
                    '--yaml': True }

        # Run the command
        scores_db.perform_get_scores(fake_responder, options)

        # Assert that the right things were called
        fake_get_scores.assert_called_once_with(1)

        # Check that the right text was output
        fake_responder.assert_called_once_with(yaml.dump({'scores':results}))
