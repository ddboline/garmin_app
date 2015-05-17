#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

HOMEDIR = os.getenv('HOME')

def run_command(command, do_popen=False, turn_on_commands=True):
    ''' wrapper around os.system '''
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        return os.popen(command)
    else:
        return os.system(command)

def convert_date(input_date):
    import datetime
    _month = int(input_date[0:2])
    _day = int(input_date[2:4])
    _year = 2000 + int(input_date[4:6])
    return datetime.date(_year, _month, _day)

def get_random_hex_string(n):
    ''' use os.urandom to create n byte random string, output integer '''
    from binascii import b2a_hex
    return int(b2a_hex(os.urandom(n)), 16)

def print_h_m_s(second):
    ''' convert time from seconds to hh:mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    return '%02i:%02i:%02i' % (hours, minutes, seconds)

def print_m_s(second):
    ''' convert time from seconds to mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    if hours == 0:
        return '%02i:%02i' % (minutes, seconds)
    else:
        return '%02i:%02i:%02i' % (hours, minutes, seconds)

def datetimefromstring(tstr, ignore_tz=False):
    import dateutil.parser
    return dateutil.parser.parse(tstr, ignoretz=ignore_tz)

def openurl(url_):
    try:
        from ssl import SSLContext, PROTOCOL_TLSv1
    except ImportError:
        SSLContext = None
        PROTOCOL_TLSv1 = None
    from urllib2 import urlopen
    
    if SSLContext is None:
        return urlopen(url_)
    else:
        gcontext = SSLContext(PROTOCOL_TLSv1)
        return urlopen(url_, context=gcontext)
