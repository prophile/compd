"""Team database."""

import redis_client
import control

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

roster = TeamDB()

