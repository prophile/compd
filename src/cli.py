"""compd-cli

Usage:
  cli.py [options] <command-detail>...

Options:
  -h --help                 Display this help.
  --yaml                    Call the command with a --yaml option
  -c <file> --config <file> Use an alternative config.yaml.
"""

from docopt import docopt
import os.path
import socket

import config

options = docopt(__doc__)

config.load_config(options['--config'])

soc = socket.socket()
soc.connect(('localhost', config.control_port))

back = soc.recv(7)
assert back == "Hello!\n", "Failed to establish connection (got '{0}')".format(back)

cmd_details = options['<command-detail>']
if options['--yaml']:
    cmd_details.append('--yaml')
cmd = ' ' .join(cmd_details) + "\n"
#print cmd
soc.send(cmd)
while True:
    back = soc.recv(256)
    print back,
    if len(back) < 256:
        break
