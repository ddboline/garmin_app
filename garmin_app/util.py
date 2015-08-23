# -*- coding: utf-8 -*-
""" Utility functions """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from subprocess import call, Popen, PIPE

HOSTNAME = os.uname()[1]
HOMEDIR = os.getenv('HOME')

class PopenWrapperClass(object):
    """ context wrapper around subprocess.Popen """
    def __init__(self, command):
        """ init fn """
        self.command = command
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE,
                          close_fds=True)

    def __enter__(self):
        """ enter fn """
        return self.pop_

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        if hasattr(self.pop_, '__exit__'):
            efunc = getattr(self.pop_, '__exit__')
            return efunc(exc_type, exc_value, traceback)
        else:
            self.pop_.wait()
            if exc_type or exc_value or traceback:
                return False
            else:
                return True

def run_command(command, do_popen=False, turn_on_commands=True,
                single_line=False):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        return PopenWrapperClass(command)
    elif single_line:
        with PopenWrapperClass(command) as pop_:
            return pop_.stdout.read()
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
    """ dump url to file """
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

import socket
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
        else:
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
        else:
            return True

def walk_wrapper(direc, callback, arg):
    """ wrapper around walk to allow consistent execution for py2/py3 """
    if hasattr(os.path, 'walk'):
        return os.path.walk(direc, callback, arg)
    elif hasattr(os, 'walk'):
        for dirpath, dirnames, filenames in os.walk(direc):
            callback(arg, dirpath, dirnames + filenames)
    return

class OpenPostgreSQLsshTunnel(object):
    """ Class to let us open an ssh tunnel, then close it when done """
    def __init__(self):
        self.tunnel_process = None

    def __enter__(self):
        import shlex, time
        if HOSTNAME != 'dilepton-tower':
            _cmd = 'ssh -N -L localhost:5432:localhost:5432 ' \
                   + 'ddboline@ddbolineathome.mooo.com'
            args = shlex.split(_cmd)
            self.tunnel_process = Popen(args, shell=False)
            time.sleep(5)
        return self.tunnel_process

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tunnel_process:
            self.tunnel_process.kill()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True

def test_datetimefromstring():
    import datetime
    from pytz import UTC
    dt0 = '1980-11-17T05:12:13Z'
    dt1 = datetime.datetime(year=1980, month=11, day=17, hour=5, minute=12, second=13, tzinfo=UTC)
    assert datetimefromstring(dt0) == dt1
