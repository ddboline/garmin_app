#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    Daemon for garmin_app
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

from garmin_app.util import OpenUnixSocketServer, OpenSocketConnection

GARMIN_SOCKET_FILE = '/tmp/.garmin_test_socket'


def handle_connection(conn, msg_q):
    from garmin_app.garmin_utils import (garmin_parse_arg_list, BASEDIR, CACHEDIR)
    recv_ = conn.recv(1024)

    script_path = '%s/garmin_app' % BASEDIR
    cache_dir = CACHEDIR

    args = recv_.split()
    isprev = False
    if not args:
        return

    if args[0] == 'prev':
        isprev = True
        args.pop(0)

    if msg_q is not None and isprev:
        tmp_ = ' '.join(args)
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

    options = {
        'do_plot': False,
        'do_year': False,
        'do_month': False,
        'do_week': False,
        'do_day': False,
        'do_file': False,
        'do_sport': None,
        'do_update': False,
        'do_average': False
    }
    options['script_path'] = script_path
    options['cache_dir'] = cache_dir

    garmin_parse_arg_list(args, msg_q=msg_q, options=options)

    if msg_q is not None and not isprev:
        if recv_.strip() != 'prev year':
            msg_q.append(recv_.strip())

    conn.send('done')


def server_thread(socketfile=GARMIN_SOCKET_FILE, msg_q=None):
    """
        server_thread, listens for commands, sends back responses.
    """
    with OpenUnixSocketServer(socketfile) as sock:
        while True:
            try:
                with OpenSocketConnection(sock) as conn:
                    handle_connection(conn, msg_q)
            except KeyboardInterrupt:
                print('exiting')
                exit(0)
    return 0


if __name__ == '__main__':
    from garmin_app.garmin_server import garmin_server

    with garmin_server():
        pass
