#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Garmin Server Class
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import multiprocessing
from .garmin_daemon import server_thread, GARMIN_SOCKET_FILE


class GarminServer(object):
    """ Garmin Server Class """
    def __init__(self):
        """ Init Method """
        self.msg_q = None
        self.net = None

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.join_server()

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
