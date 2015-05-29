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
    requests.packages.urllib3.disable_warnings()

    urlout = requests.get(url_, verify=False)
    if urlout.status_code != 200:
        print('something bad happened %d' % urlout.status_code)
        raise HTTPError
    return urlout.text.split('\n')

def dump_to_file(url_, outfile_):
    from contextlib import closing
    import requests
    from requests import HTTPError
    requests.packages.urllib3.disable_warnings()
    with closing(requests.get(url_, stream=True, verify=False)) as url_:
        if url_.status_code != 200:
            print('something bad happened %d' % url_.status_code)
            raise HTTPError        
        for chunk in url_.iter_content(4096):
            outfile_.write(chunk)
    return True
            