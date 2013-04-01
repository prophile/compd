"""Team database."""

import redis_client
import control
from twisted.internet import defer
import re

class TeamDB(object):
    """A team database."""

    def __init__(self):
        """Default constructor."""
        pass

    def add(self, tla, college, name):
        """Add a team into the database."""
        redis_client.connection.set('team:{0}:college'.format(tla),
                                    college)
        redis_client.connection.set('team:{0}:name'.format(tla),
                                    name)
        # We initially have the notes empty to be filled in later
        redis_client.connection.set('team:{0}:notes'.format(tla),
                                    '')
        # Fill in presence when teams arrive
        redis_client.connection.set('team:{0}:present'.format(tla),
                                    'no')

    def delete(self, tla):
        """Delete a team from the database entirely.

        This is probably not what you want unless you added one by accident."""
        # Remove all keys
        for key in ('college', 'name', 'notes', 'present'):
            redis_client.connection.delete('team:{0}:{1}'.format(tla, key))
        # TODO: interact with other systems

    def update(self, tla, college = None, name = None, notes = None):
        """Update team details in the DB."""
        for key, value in {'college': college,
                           'name': name,
                           'notes': notes}.iteritems():
            if value is None:
                continue
            redis_client.connection.set('team:{0}:{1}'.format(tla, key),
                                        value)

    # Presence is used, among other things, for determining whether a team
    # will be included in the match scheduling pool.
    def mark_present(self, tla):
        """Mark a given team present."""
        # TODO: check the team actually exists
        redis_client.connection.set('team:{0}:present'.format(tla), 'yes')

    def mark_absent(self, tla):
        """Mark a given team absent."""
        # TODO: check the team actually exists
        redis_client.connection.set('team:{0}:present'.format(tla), 'no')

    @defer.inlineCallbacks
    def list(self):
        # Take a census of team:*:college keys
        keys = yield redis_client.connection.keys('team:*:college')
        defer.returnValue([re.match('team:([a-zA-Z0-9]*):college', key).group(1)
                             for key in keys])

    @defer.inlineCallbacks
    def get(self, team):
        # Return team info dict
        college, name, notes, present = \
            yield redis_client.connection.mget(*['team:{0}:{1}'.format(team, x)
                                                   for x in ('college',
                                                             'name',
                                                             'notes',
                                                             'present')])
        defer.returnValue({'college': college,
                           'name': name,
                           'notes': notes,
                           'present': present == 'yes'})

roster = TeamDB()

