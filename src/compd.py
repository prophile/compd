"""compd

Usage:
  compd.py [options]

Options:
  --version                  Print the version, and exit.
  -h --help                 Display this help.
  -c <file> --config <file> Use an alternative config.yaml.
"""

from docopt import docopt
from subprocess import check_output
import config
import sys
import control_socket
from twisted.internet import reactor, task

GIT_VERSION = check_output(('git', 'describe', '--always')).strip()
VERSION = 'compd {0}'.format(GIT_VERSION)

options = docopt(__doc__, version = VERSION)

config.load_config(options['--config'])

if not config.run:
    print >>sys.stderr, "config.yaml demands that we immediately halt"
    sys.exit(1)

def print_message():
    print config.message

task.LoopingCall(print_message).start(1.5)

control_socket.install_control_handler()

reactor.run()

