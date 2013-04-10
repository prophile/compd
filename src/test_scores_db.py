import scores_db
import mock
import redis_client
import control
from twisted.internet import defer

def test_set_scores():
    fake_connection = mock.Mock()
    fake_connection.set = mock.Mock()
    with mock.patch('redis_client.connection', fake_connection):
        scores_db.scores.set_match_score(1, 'ABC', 12)
        fake_connection.set.assert_called_once_with('comp:scores:1:ABC:game', 12)
