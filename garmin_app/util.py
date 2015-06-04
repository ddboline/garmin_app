# -*- coding: utf-8 -*-
""" Utility functions """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')

def run_command(command, do_popen=False, turn_on_commands=True):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        return Popen(command, shell=True, stdout=PIPE, close_fds=True).stdout
    else:
        return call(command, shell=True)

def convert_date(input_date):
    """
        convert string to datetime object
        (why not just use dateutil.parser.parse?)
    """
    import datetime
    _month = int(input_date[0:2])
    _day = int(input_date[2:4])
    _year = 2000 + int(input_date[4:6])
    return datetime.date(_year, _month, _day)

def print_h_m_s(second):
    """ convert time from seconds to hh:mm:ss format """
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    return '%02i:%02i:%02i' % (hours, minutes, seconds)

def datetimefromstring(tstr, ignore_tz=False):
    """ wrapper around dateutil.parser.parse """
    from dateutil.parser import parse
    return parse(tstr, ignoretz=ignore_tz)

def openurl(url_):
    """ wrapper around requests.get.text simulating urlopen """
    import requests
    from requests import HTTPError
    try:
        requests.packages.urllib3.disable_warnings()
    except AttributeError:
        pass
    urlout = requests.get(url_, verify=False)
    if urlout.status_code != 200:
        print('something bad happened %d' % urlout.status_code)
        raise HTTPError
    return urlout.text.split('\n')

def dump_to_file(url_, outfile_):
    from contextlib import closing
    import requests
    from requests import HTTPError
    try:
        requests.packages.urllib3.disable_warnings()
    except AttributeError:
        pass
    with closing(requests.get(url_, stream=True, verify=False)) as url_:
        if url_.status_code != 200:
            print('something bad happened %d' % url_.status_code)
            raise HTTPError        
        for chunk in url_.iter_content(4096):
            outfile_.write(chunk)
    return True

import socket, time
class OpenUnixSocketServer(object):
    def __init__(self, socketfile):
        self.sock = None
        self.socketfile = socketfile
        if os.path.exists(socketfile):
            os.remove(socketfile)
        return

    def __enter__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.bind(self.socketfile)
            os.chmod(self.socketfile, 0o777)
        except:
            time.sleep(10)
            print('failed to open socket')
            return self.__enter__()
        print('open socket')
        self.sock.listen(0)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


class OpenSocketConnection(object):
    def __init__(self, sock):
        self.sock = sock

    def __enter__(self):
        self.conn, _ = self.sock.accept()
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True
