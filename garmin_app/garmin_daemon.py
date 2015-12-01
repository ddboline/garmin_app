#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Daemon for garmin_app
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from garmin_app.util import OpenUnixSocketServer, OpenSocketConnection

GARMIN_SOCKET_FILE = '/tmp/.garmin_test_socket'


def server_thread(socketfile=GARMIN_SOCKET_FILE, msg_q=None):
    """
        server_thread, listens for commands, sends back responses.
    """
    from garmin_app.garmin_utils import garmin_parse_arg_list, BASEDIR, CACHEDIR

    script_path = '%s/garmin_app' % BASEDIR
    cache_dir = CACHEDIR

    with OpenUnixSocketServer(socketfile) as sock:
        while True:
            with OpenSocketConnection(sock) as conn:
                recv_ = conn.recv(1024)

                args = recv_.split()
                isprev = False
                if not args:
                    continue

                if args[0] == 'prev':
                    isprev = True
                    args.pop(0)

                if msg_q is not None:
                    print(msg_q)

                if msg_q is not None and isprev:
                    tmp_ = ' '.join(args)
                    print(tmp_, msg_q)
                    if tmp_ in msg_q:
                        idx = msg_q.index(tmp_)
                        print('msg_q', msg_q, idx)
                        if idx > 0:
                            msg_q = msg_q[0:idx]
                        elif idx == 0:
                            while len(msg_q) > 1:
                                msg_q.pop(-1)
                    if tmp_ == 'year':
                        while len(msg_q) > 0:
                            msg_q.pop(-1)

                options = {'do_plot': False, 'do_year': False,
                           'do_month': False, 'do_week': False,
                           'do_day': False, 'do_file': False,
                           'do_sport': None, 'do_update': False,
                           'do_average': False}
                options['script_path'] = script_path
                options['cache_dir'] = cache_dir

                garmin_parse_arg_list(args, msg_q=msg_q, options=options)

                if msg_q is not None and not isprev:
                    if recv_.strip() != 'prev year':
                        msg_q.append(recv_.strip())

                if msg_q is not None:
                    print(msg_q)

                conn.send('done')
    return 0

if __name__ == '__main__':
    from garmin_app.garmin_server import GarminServer

    with GarminServer():
        pass
