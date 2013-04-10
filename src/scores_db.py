"""Team scores database."""

from uuid import uuid4
import redis_client
import control
import re
from twisted.internet import defer

import ranker

class ScoresDB(object):
    """A scores database."""
    def __init__(self):
        """Default constructor."""
        pass

    def set_match_score(self, match, tla, match_score):
        """Sets the score for a given team in a given match."""
        redis_client.connection.set('comp:scores:{0}:{1}:game'.format(match, tla),
                                    match_score)

    def set_league_points(self, match, points):
        """Sets the league points for all the teams in a given match."""

        keys = ['comp:scores:{0}:{1}:league'.format(match, tla) for tla in points.keys()]
        keyed_points = dict(zip(keys, points.values()))

        redis_client.connection.mset(keyed_points)

    @defer.inlineCallbacks
    def get_league_points(self, tla):
        """Gets the league points a given team."""

        keys = yield redis_client.connection.keys('comp:scores:*:{0}:league'.format(tla))
        if len(keys) == 0:
            defer.returnValue(None)
        points = yield redis_client.connection.mget(*keys)
        defer.returnValue(sum(points))

    def disqualify(self, match, tla):
        """Disqualifies a given team in a given match."""
        redis_client.connection.set('comp:scores:{0}:{1}:dsq'.format(match, tla), True)

    def re_qualify(self, match, tla):
        """Re-qualifies a given team in a given match.
        Just in case a judge changes their mind."""
        redis_client.connection.delete('comp:scores:{0}:{1}:dsq'.format(match, tla))

    @defer.inlineCallbacks
    def teams_in_match(self, match):
        # Get a list of the teams in a given match for which we have game scores
        keys = yield redis_client.connection.keys('comp:scores:{0}:*:game'.format(match))
        teams = [re.match('comp:scores:{0}:([a-zA-Z0-9]*):game'.format(match), key).group(1)
                             for key in keys]
        defer.returnValue(teams)

    @defer.inlineCallbacks
    def teams_disqualified_in_match(self, match):
        # Get a list of the teams disqualified in a given match
        keys = yield redis_client.connection.keys('comp:scores:{0}:*:dsq'.format(match))
        teams = [re.match('comp:scores:{0}:([a-zA-Z0-9]*):dsq'.format(match), key).group(1)
                             for key in keys]
        defer.returnValue(teams)

    @defer.inlineCallbacks
    def get_match_scores(self, match):
        # Get a dictionary of team => game points for a given match
        teams = yield self.teams_in_match(match)
        if len(teams) == 0:
            defer.returnValue(None)

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
def perform_set_score(responder, options):
    """Handle the `set-score` command."""
    match = options['<match-id>']
    tla = options['<tla>']
    score = options['<score>']
    scores.set_match_score(match, tla, score)
    responder('Scored {0} points for {1} in match {2}'.format(score, tla, match))

@control.handler('get-score')
@defer.inlineCallbacks
def perform_get_score(responder, options):
    """Handle the `get-score` command."""
    match = options['<match-id>']
    tla = options['<tla>']
    score = yield scores.get_match_score(match, tla)
    responder('Team {0} scored {1} in match {2}'.format(tla, score, match))

@control.handler('get-scores')
@defer.inlineCallbacks
def perform_get_scores(responder, options):
    """Handle the `get-scores` command."""
    match = options['<match-id>']
    all_scores = yield scores.get_match_scores(match)
    for tla, score in all_scores.iteritems():
        responder('Team {0} scored {1} in match {2}'.format(tla, score, match))

@control.handler('calc-league-points')
@defer.inlineCallbacks
def perform_calc_league_points(responder, options):
    """Handle the `calc-league-points` command."""
    match = options['<match-id>']
    match_scores = yield scores.get_match_scores(match)
    if match_scores is None:
        responder('No scores available for match {0}'.format(match))
        return
    dsq_teams = yield scores.teams_disqualified_in_match(match)
    league_points = ranker.get_ranked_points(match_scores, dsq_teams)
    scores.set_league_points(match, league_points)
    for tla, pts in league_points.iteritems():
        responder('Team {0} earned {1} points from match {2}'.format(tla, pts, match))

@control.handler('get-league-points')
@defer.inlineCallbacks
def perform_get_league_points(responder, options):
    """Handle the `get-league-points` command."""
    tla = options['<tla>']
    league_points = yield scores.get_league_points(tla)
    print league_points
    if league_points is None:
        responder('No scores available for team {0}'.format(tla))
        return
    responder('Team {0} have {1} league points'.format(tla, league_points))
