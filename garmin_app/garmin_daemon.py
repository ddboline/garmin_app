#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Daemon for garmin_app
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import multiprocessing
import socket

GARMIN_SOCKET_FILE = '/tmp/.garmin_test_socket'

def server_thread(socketfile=GARMIN_SOCKET_FILE, msg_q=None):
    """
        server_thread, listens for commands, sends back responses.
    """
    from garmin_app.garmin_utils import garmin_parse_arg_list

    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])

    if os.path.exists(socketfile):
        os.remove(socketfile)
    sock_ = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock_.bind(socketfile)
        os.chmod(socketfile, 0o777)
    except socket.error:
        time.sleep(10)
        print('try again to open socket')
        return server_thread(socketfile, msg_q)
    print('socket open')
    sock_.listen(0)

    while True:
        conn, _ = sock_.accept()
        recv_ = conn.recv(1024)

        args = recv_.split()
        isprev = False
        if not args:
            continue

        if args[0] == 'prev':
            isprev = True
            args.pop(0)

        if msg_q != None:
            print(msg_q)

        if msg_q != None and isprev:
            _tmp = ' '.join(args)
            if _tmp in msg_q:
                idx = msg_q.index(_tmp)
                print('msg_q', msg_q, idx)
                if idx > 0:
                    msg_q = msg_q[0:idx]
                elif idx == 0:
                    while len(msg_q) > 1:
                        msg_q.pop(-1)
            if _tmp == 'year':
                while len(msg_q) > 0:
                    msg_q.pop(-1)

        options = {'do_plot': False, 'do_year': False, 'do_month': False,
                   'do_week': False, 'do_day': False, 'do_file': False,
                   'do_sport': None, 'do_update': False, 'do_average': False}
        options['script_path'] = script_path

        garmin_parse_arg_list(args, msg_q, **options)

        if msg_q != None and not isprev:
            if recv_.strip() != 'prev year':
                msg_q.append(recv_.strip())

        if msg_q != None:
            print(msg_q)

        conn.send('done')
        conn.close()
    sock_.shutdown(socket.SHUT_RDWR)
    sock_.close()
    return 0

class GarminServer(object):
    """ Garmin Server Class """
    def __init__(self):
        """ Init Method """
        self.msg_q = None
        self.net = None
        pass

    def start_server(self):
        """ start server, manager based communication """
        manager = multiprocessing.Manager()
        self.msg_q = manager.list()
        self.net = multiprocessing.Process(target=server_thread,
                                           args=(GARMIN_SOCKET_FILE,
                                                 self.msg_q))
        self.net.start()
    
    def join_server(self):
        self.net.join()

if __name__ == '__main__':
    gsrv = GarminServer()
    gsrv.start_server()
    gsrv.join_server()
