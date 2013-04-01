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
        redis_client.connection.publish('team:update', 'update')

    def delete(self, tla):
        """Delete a team from the database entirely.

        This is probably not what you want unless you added one by accident."""
        # Remove all keys
        for key in ('college', 'name', 'notes', 'present'):
            redis_client.connection.delete('team:{0}:{1}'.format(tla, key))
        # TODO: interact with other systems
        redis_client.connection.publish('team:update', 'update')

    def update(self, tla, college = None, name = None, notes = None):
        """Update team details in the DB."""
        for key, value in {'college': college,
                           'name': name,
                           'notes': notes}.iteritems():
            if value is None:
                continue
            redis_client.connection.set('team:{0}:{1}'.format(tla, key),
                                        value)
        redis_client.connection.publish('team:update', 'update')

    # Presence is used, among other things, for determining whether a team
    # will be included in the match scheduling pool.
    def mark_present(self, tla):
        """Mark a given team present."""
        # TODO: check the team actually exists
        redis_client.connection.set('team:{0}:present'.format(tla), 'yes')
        redis_client.connection.publish('team:update', 'update')

    def mark_absent(self, tla):
        """Mark a given team absent."""
        # TODO: check the team actually exists
        redis_client.connection.set('team:{0}:present'.format(tla), 'no')
        redis_client.connection.publish('team:update', 'update')

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

@control.handler('team')
@defer.inlineCallbacks
def perform_team(responder, options):
    tla = options['<tla>']
    team = yield roster.get(options['<tla>'])
    responder('{0}: {1}'.format(tla, team['name']))
    responder('    College: {0}'.format(team['college']))
    responder('    ' + ('PRESENT' if team['present'] else 'ABSENT'))
    if team['notes']:
        responder(str(team['notes']))

@control.handler('list-teams')
@defer.inlineCallbacks
def perform_list_teams(responder, options):
    list = yield roster.list()
    if not list:
        responder('No teams in database.')
    for tla in list:
        info = yield roster.get(tla)
        responder('{0}: {1}'.format(tla, info['name']))

@control.handler('add-team')
def perform_add_team(responder, options):
    roster.add(options['<tla>'],
               options['<college>'],
               options['<name>'])
    responder('Team {0} added.'.format(options['<tla>']))

@control.handler('del-team')
def perform_add_team(responder, options):
    roster.delete(options['<tla>'])
    responder('Team {0} dropped.'.format(options['<tla>']))

@control.handler('set-team-present')
def perform_set_team_present(responder, options):
    roster.mark_present(options['<tla>'])
    responder('Team {0} marked present.'.format(options['<tla>']))

@control.handler('set-team-absent')
def perform_set_team_absent(responder, options):
    roster.mark_absent(options['<tla>'])
    responder('Team {0} marked absent.'.format(options['<tla>']))

@control.handler('set-team-name')
def perform_set_team_name(responder, options):
    roster.update(options['<tla>'],
                  name = options['<name>'])
    responder('Team {0} updated.'.format(options['<tla>']))

@control.handler('set-team-college')
def perform_set_team_college(responder, options):
    roster.update(options['<tla>'],
                  college = options['<college>'])
    responder('Team {0} updated.'.format(options['<tla>']))

@control.handler('set-team-notes')
def perform_set_team_notes(responder, options):
    roster.update(options['<tla>'],
                  notes = options['<notes>'])
    responder('Team {0} updated.'.format(options['<tla>']))

@control.handler('append-note')
@defer.inlineCallbacks
def perform_append_notes(responder, options):
    team = yield roster.get(options['<tla>'])
    notes = team['notes']
    # add a full stop if there isn't one
    if notes and notes[-1] not in '.?!':
        notes += '.'
    notes += ' {0}'.format(options['<note>'])
    roster.update(options['<tla>'],
                  notes = notes)
    responder('Team {0} notes updated.'.format(options['<tla>']))

