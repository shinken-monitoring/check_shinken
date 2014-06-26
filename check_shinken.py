#!/usr/bin/env python
#
# Copyright (C) 2009-2011:
#    Denis GERMAIN, dt.germain@gmail.com
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
"""
check_shinken.py:
    This check is getting daemons state from a arbiter connection.
    """

import os
import socket
from optparse import OptionParser

# Exit statuses recognized by Nagios and thus by Shinken
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

# Name of the Pyro Object we are searching
PYRO_OBJECT = 'ForArbiter'
daemon_types = {'arbiter':7770, 'broker':7772, 'scheduler':7768, 'reactionner':7769, 'poller':7771, 'receiver':7773 }


## Try to import all Shinken stuff
try:
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    if not hasattr(os, "getuid") or os.getuid() != 0:
        imp.load_module('shinken', *imp.find_module('shinken', [".", ".."]))

try:
    from shinken.http_client import HTTPClient, HTTPExceptions
except ImportError, exp:
    print ('CRITICAL : check_shinken requires the Python Pycurl module.'
            'Please install it. (%s)' % exp)
    raise SystemExit(CRITICAL)


# Adding options. None are required, check_shinken will use shinken defaults
# TODO: Add more control in args problem and usage than the default
# OptionParser one
parser = OptionParser()
parser.add_option('-a', '--hostname', dest='hostname', default='127.0.0.1')
parser.add_option('-p', '--portnumber', dest='portnum', default=0)
parser.add_option('-s', '--ssl', dest='ssl', default=False)
# TODO: Add a list of correct values for target and don't authorize
# anything else
#parser.add_option('-t', '--target', dest='target')
parser.add_option('-d', '--daemonname', dest='daemon', default='')
# In HA architectures, a warning should be displayed if there's one
# daemon down
parser.add_option('-w', '--warning', dest='warning', default=1, type=int)
# If no deamon is left, display a critical (but shinken will be
# probably dead already)
parser.add_option('-c', '--critical', dest='critical', default=0, type=int)
parser.add_option('-T', '--timeout', dest='timeout', default=10, type=float)
parser.add_option('-D', '--data-timeout', dest='data_timeout', default=10, type=float)

# Retrieving options
options, args = parser.parse_args()
# TODO: for now, helpme doesn't work as desired
options.helpme = False

# Set the default socket connection to the timeout, by default it's 10s
socket.setdefaulttimeout(float(options.timeout))


daemon=options.daemon

if daemon not in daemon_types:
    print 'CRITICAL - ', daemon, 'is not a Shinken daemon!'
    parser.print_help()
    raise SystemExit(CRITICAL)

port=options.portnum
if port==0:
    port=daemon_types[daemon]

con = None
try:
    con = HTTPClient(address=options.hostname, port=port,  timeout=options.timeout, data_timeout=options.data_timeout, use_ssl=options.ssl)
    result=con.get('ping')
except Exception, exp:
    print "CRITICAL : the %s is not reachable : (%s)." % (daemon,exp)
    raise SystemExit(CRITICAL)


if result:
   if result=='pong':
       print 'OK - ', daemon, 'alive'
       raise SystemExit(OK)
   else:
       print 'CRITICAL -', daemon, ' down'
       raise SystemExit(CRITICAL)
else:
    print 'UNKNOWN - %s status could not be retrieved' % daemon
    raise SystemExit(UNKNOWN)

