"""compctl

Usage:
  compctl halt
  compctl usage

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
        return fn
    return wrapper

def dispatch(options, responder):
    for name, callback in HANDLERS.iteritems():
        if options[name]:
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
    import sys
    responder("System going down for halt")
    sys.exit(0)

def default_responder(output):
    print output

def handle(cmd, responder = default_responder, no_auto_fail = False):
    try:
        dispatch(parse(cmd), responder)
    except CommandError:
        if no_auto_fail:
            raise
        else:
            handle('usage', responder, no_auto_fail = True)
