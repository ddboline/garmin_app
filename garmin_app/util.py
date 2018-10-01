# -*- coding: utf-8 -*-
""" Utility functions """
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import time
import shlex
import socket
import numpy as np
from subprocess import call, Popen, PIPE
from pytz import timezone
from time import strftime

HOSTNAME = os.uname()[1]
HOMEDIR = os.getenv('HOME')
USER = 'ddboline'

POSTGRESTRING = 'postgresql://%s:BQGIvkKFZPejrKvX@localhost' % USER

utc = timezone('UTC')
est = timezone(strftime("%Z").replace('CST', 'CST6CDT').replace('EDT', 'EST5EDT'))


class PopenWrapperClass(object):
    """ context wrapper around subprocess.Popen """

    def __init__(self, command):
        """ init fn """
        self.command = command
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE)

    def __iter__(self):
        return self.pop_.stdout

    def __enter__(self):
        """ enter fn """
        return self.pop_.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        if hasattr(self.pop_, '__exit__'):
            efunc = getattr(self.pop_, '__exit__')
            return efunc(exc_type, exc_value, traceback)
        else:
            self.pop_.wait()
            if exc_type or exc_value or traceback:
                return False
            return True


def run_command(command, do_popen=False, turn_on_commands=True, single_line=False):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        if single_line:
            with PopenWrapperClass(command) as pop_:
                return pop_.read()
        return PopenWrapperClass(command)
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


def dump_to_file(url, outfile_):
    """ dump url to file """
    from contextlib import closing
    import requests
    from requests import HTTPError
    try:
        requests.packages.urllib3.disable_warnings()
    except AttributeError:
        pass
    with closing(requests.get(url, stream=True, verify=False)) as url_:
        if url_.status_code != 200:
            print('something bad happened %d, %s' % (url_.status_code, url))
            raise HTTPError
        for chunk in url_.iter_content(4096):
            outfile_.write(chunk)
    return True


class OpenUnixSocketServer(object):
    """ context wrapper around unix socket """

    def __init__(self, socketfile):
        """ init fn """
        self.sock = None
        self.socketfile = socketfile
        if os.path.exists(socketfile):
            os.remove(socketfile)

    def __enter__(self):
        """ enter fn """
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.socketfile)
        os.chmod(self.socketfile, 0o777)
        print('open socket')
        self.sock.listen(0)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        return True


class OpenSocketConnection(object):
    """ context wrapper around socket connection """

    def __init__(self, sock):
        """ init fn """
        self.sock = sock
        self.conn, _ = self.sock.accept()

    def __enter__(self):
        """ enter fn """
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        self.conn.close()
        if exc_type or exc_value or traceback:
            return False
        return True


class OpenUnixSocketClient(object):

    def __init__(self, host='localhost', portno=10888, socketfile='/tmp/.record_roku_socket'):
        self.sock = None
        self.socketfile = None
        self.host = host
        self.portno = portno
        if socketfile:
            self.socketfile = socketfile

    def __enter__(self):
        stm_type = socket.SOCK_STREAM
        if self.socketfile:
            net_type = socket.AF_UNIX
            addr_obj = self.socketfile
        else:
            net_type = socket.AF_INET
            addr_obj = (self.host, self.portno)
        self.sock = socket.socket(net_type, stm_type)
        try:
            err = self.sock.connect(addr_obj)
        except socket.error:
            return None
        if err:
            print(err)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        return True


def send_command(ostr, host='localhost', portno=10888, socketfile='/tmp/.record_roku_socket'):
    ''' send string to specified socket '''
    with OpenUnixSocketClient(host, portno, socketfile) as sock:
        if not sock:
            return 'Failed to open socket'
        sock.send(b'%s\n' % ostr)
        return sock.recv(1024)


def walk_wrapper(direc, callback, arg):
    """ wrapper around walk to allow consistent execution for py2/py3 """
    if hasattr(os.path, 'walk'):
        return os.path.walk(direc, callback, arg)
    elif hasattr(os, 'walk'):
        for dirpath, dirnames, filenames in os.walk(direc):
            callback(arg, dirpath, dirnames + filenames)
    return


def haversine_distance(lat1, lon1, lat2, lon2):
    r_earth = 6371.
    dlat = np.abs(lat1 - lat2) * np.pi / 180.
    dlon = np.abs(lon1 - lon2) * np.pi / 180.
    lat1 *= np.pi / 180.
    lat2 *= np.pi / 180.
    dist = (2. * r_earth * np.arcsin(
        np.sqrt(np.sin(dlat / 2.)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.)**2)))
    return dist


class OpenPostgreSQLsshTunnel(object):
    """ Class to let us open an ssh tunnel, then close it when done """

    def __init__(self, port=5432, do_tunnel=False):
        self.tunnel_process = 0
        self.postgre_port = 5432
        self.remote_port = port
        self.do_tunnel = do_tunnel

    def __enter__(self):
        if HOSTNAME not in ('dilepton-tower', 'dilepton-chromebook') and \
                self.do_tunnel:
            self.postgre_port = self.remote_port
            _cmd = 'ssh -N -L localhost:%d' % self.remote_port + \
                   ':localhost:5432 ddboline@home.ddboline.net'
            args = shlex.split(_cmd)
            self.tunnel_process = Popen(args, shell=False)
            time.sleep(5)
        return self.postgre_port

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tunnel_process:
            self.tunnel_process.kill()
        if exc_type or exc_value or traceback:
            return False
        return True


def test_datetimefromstring():
    """ test datetimefromstring """
    import datetime
    from pytz import UTC
    dt0 = '1980-11-17T05:12:13Z'
    dt1 = datetime.datetime(year=1980, month=11, day=17, hour=5, minute=12, second=13, tzinfo=UTC)
    assert datetimefromstring(dt0) == dt1
