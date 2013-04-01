"""compd

Usage:
  compd.py [options]

Options:
  --version                  Print the version, and exit.
  -h --help                 Display this help.
  -c <file> --config <file> Use an alternative config.yaml.
"""

from docopt import docopt
from subprocess import check_output, CalledProcessError
import config
import sys
import control
import control_socket
import control_irc
import redis_process
import redis_client
from twisted.internet import reactor, task

try:
    GIT_VERSION = check_output(('git', 'describe', '--always')).strip()
except CalledProcessError:
    GIT_VERSION = '?'
VERSION = 'compd {0}'.format(GIT_VERSION)

options = docopt(__doc__, version = VERSION)

config.load_config(options['--config'])

if not config.run:
    print >>sys.stderr, "config.yaml demands that we immediately halt"
    sys.exit(1)

def print_message():
    control.broadcast(config.message)

# Set up logging to stdout
def log_to_stdout(message):
    print message
control.subscribe(log_to_stdout)

task.LoopingCall(print_message).start(15)

def got_redis_client():
    print 'Connected to Redis server'
    control_socket.install_control_handler()
    control_irc.install_irc_handler()
    import schedule_db
    import team_db

def got_redis_server():
    redis_client.run_redis_client(got_redis_client)

redis_process.run_redis_server(got_redis_server)

reactor.run()

