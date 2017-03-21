#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Garmin Server Class
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import multiprocessing as mp
from garmin_app.garmin_daemon import server_thread, GARMIN_SOCKET_FILE
from contextlib import contextmanager


@contextmanager
def garmin_server(socketfile=GARMIN_SOCKET_FILE):
    manager = mp.Manager()
    msg_q = manager.list()
    net = mp.Process(target=server_thread, args=(socketfile, msg_q))
    net.start()
    yield net
    net.join()
