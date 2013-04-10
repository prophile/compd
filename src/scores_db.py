"""Team scores database."""

from uuid import uuid4
import redis_client
import control
import re
from twisted.internet import defer

class ScoresDB(object):
    """A scores database."""
    def __init__(self):
        """Default constructor."""
        pass

    def set_score(self, match, tla, match_score, league_points):
        """Sets the score for a given team in a given match."""
        redis_client.connection.set('comp:scores:{0}:{1}:game'.format(match, tla),
                                    match_score)
        redis_client.connection.set('comp:scores:{0}:{1}:league'.format(match, tla),
                                    league_points)
        # TODO: does this really need publishing?
        redis_client.connection.publish('comp:match', 'update')

    @defer.inlineCallbacks
    def teams_in_match(self, match):
        # Get a list of the teams in a given match
        keys = yield redis_client.connection.keys('comp:scores:{0}:*:game'.format(match))
        teams = [re.match('comp:scores:{0}:([a-zA-Z0-9]*):game'.format(match), key).group(1)
                             for key in keys]
        defer.returnValue(teams)

    @defer.inlineCallbacks
    def match_scores(self, match):
        # Get a dictionary of team => game points for a given match
        teams = yield self.teams_in_match(match)

        raw_scores = \
            yield redis_client.connection.mget(*['comp:scores:{0}:{1}:game'.format(match, tla)
                                                   for tla in teams])

        match_scores = dict(zip(teams, raw_scores))
        defer.returnValue(match_scores)

    @defer.inlineCallbacks
    def get_match_score(self, match, tla):
        """Gets the score for a given team in a given match.

        Returns something"""
        value = yield redis_client.connection.get('comp:scores:{0}:{1}:game'.format(match, tla))
        defer.returnValue(value)

scores = ScoresDB()

@control.handler('set-score')
@defer.inlineCallbacks
def perform_set_scores(responder, options):
    """Handle the `set-score` command."""
    match = options['<match-id>']
    tla = options['<tla>']
    score = options['<score>']
    scores.set_score(match, tla, score, 0)
    responder('Scored {0} points for {1} in match {2}'.format(score, tla, match))
    match_scores = yield scores.match_scores(match)
    print match_scores
