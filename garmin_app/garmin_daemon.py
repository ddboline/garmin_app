#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os, glob
import datetime
from garmin_app.garmin_utils import garmin_parse_arg_list
from util import run_command
import multiprocessing
import socket

#BASEURL = 'https://ddbolineathome.mooo.com/~ddboline'
BASEURL = 'http://ddbolineinthecloud.mooo.com/~ubuntu'

GARMIN_SOCKET_FILE = '/tmp/.garmin_test_socket'

def server_thread(socketfile=GARMIN_SOCKET_FILE, msg_q=None):
    '''
        server_thread, listens for commands, sends back responses.
    '''
    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])
    
    if os.path.exists(socketfile):
        os.remove(socketfile)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.bind(socketfile)
        os.chmod(socketfile, 0o777)
    except socket.error:
        time.sleep(10)
        print('try again to open socket')
        return server_thread(socketfile, msg_q)
    print('socket open')
    s.listen(0)

    net_pid = -1
    while True:
        outstring = []
        c, a = s.accept()
        d = c.recv(1024)

        args = d.split()
        
        gdir = []
        options = {'do_plot': False, 'do_year': False, 'do_month': False, 'do_week': False, 'do_day': False, 'do_file': False, 'do_sport': None, 'do_update': False, 'do_average': False}
        options['script_path'] = script_path

        garmin_parse_arg_list(args, **options)
        c.send('done')
        c.close()
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    return 0

class GarminServer(object):
    def __init__(self):
        self.msg_q = None
        self.net = None
        pass

    def start_server(self):
        self.msg_q = multiprocessing.Queue()
        self.net = multiprocessing.Process(target=server_thread, args=(GARMIN_SOCKET_FILE, self.msg_q))
        self.net.start()
        self.net.join()

if __name__ == '__main__':
    g = GarminServer()
    g.start_server()
