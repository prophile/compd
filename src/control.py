"""compctl

Usage:
  compctl halt
  compctl usage
  compctl schedule (lunch | league | knockout | open | briefing | photo | prizes | tinker) <time>
  compctl unschedule <id>
  compctl show-schedule <from> <to>
  compctl add-team <tla> <name> <college>
  compctl del-team <tla>
  compctl set-team-name <tla> <name>
  compctl set-team-college <tla> <college>
  compctl set-team-notes <tla> <notes>
  compctl append-note <tla> <note>
  compctl set-team-present <tla>
  compctl set-team-absent <tla>
  compctl list-teams
  compctl team <tla>
  compctl screen-list
  compctl screen-set-mode <id> <mode>
  compctl screen-override <id> <message>
  compctl screen-clear-override <id>
  compctl set-score <match-id> <tla> <score>
  compctl get-score [--yaml] <match-id> <tla>
  compctl get-scores [--yaml] <match-id>
  compctl calc-league-points [--yaml] <match-id>
  compctl get-league-points [--yaml] <tla>
  compctl add-match [--knockout] <name> <time>
  compctl del-match <name>
  compctl set-match-teams <name> <team>...
  compctl clear-match-teams <name>
  compctl list-matches <from> <to>

"""

import shlex
import re
from docopt import docopt, DocoptExit

class CommandError(Exception):
    pass

def parse(cmd):
    parts = shlex.split(cmd.strip())
    try:
        options = docopt(__doc__, argv = parts,
                         help = False, version = None)
        return options
    except DocoptExit:
        raise CommandError()

HANDLERS = {}

def handler(subcommand):
    def wrapper(fn):
        HANDLERS[subcommand] = fn
        print "Installed command: {0}".format(subcommand)
        return fn
    return wrapper

def dispatch(options, responder):
    for name, callback in HANDLERS.iteritems():
        if options.get(name):
            callback(responder, options)
            return
    raise CommandError()

@handler('usage')
def handle_usage(responder, opts):
    regex = re.compile('  compctl (.*)')
    for line in __doc__.split('\n')[3:]:
        match = regex.match(line)
        if match:
            responder('Usage: {0}'.format(match.group(1)))

@handler('halt')
def halt_system(responder, options):
    from twisted.internet import reactor
    responder("System going down for halt")
    reactor.stop()

def default_responder(output):
    print output

def handle(cmd, responder = default_responder, no_auto_fail = False,
           short_fail = False):
    try:
        dispatch(parse(cmd), responder)
    except CommandError:
        if no_auto_fail:
            raise
        elif short_fail:
            responder('Syntax error.')
        else:
            handle('usage', responder, no_auto_fail = True)

RECEIVERS = {}

def broadcast(message):
    for receiver in RECEIVERS.itervalues():
        receiver(message)

def subscribe(handler):
    key = object()
    RECEIVERS[key] = handler
    def unsubscribe():
        del RECEIVERS[key]
    return unsubscribe

