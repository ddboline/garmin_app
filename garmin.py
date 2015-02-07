#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import glob
import argparse

from garmin_app.garmin_cache import GarminCache
from garmin_app.garmin_parse import GarminParse
from garmin_app.garmin_report import GarminReport
from garmin_app.garmin_utils import compare_with_remote, garmin_parse_arg_list,\
    BASEURL, SPORT_TYPES
from garmin_app.garmin_daemon import GarminServer

try:
    from util import run_command
except ImportError:
    if os.path.exists('%s/scripts' % os.getenv('HOME')):
        os.sys.path.append('%s/scripts' % os.getenv('HOME'))
        from util import run_command

def garmin_arg_parse():
    help_text = 'usage: ./garmin.py <get|build|sync|backup|year|(file)|(directory)|(year(-month(-day)))|(sport)|occur|update>'
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('command', nargs='*', help=help_text)
    parser.add_argument('--daemon', '-d', action='store_true', help='run as daemon')
    args = parser.parse_args()

    options = ['build', 'sync', 'backup']

    #print(os.sys.argv)
    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])

    if '%s/bin' % script_path not in os.getenv('PATH'):
        os.putenv('PATH', '%s:%s/bin' % (os.getenv('PATH'), script_path))

    for arg in getattr(args, 'command'):
        if any(arg == x for x in ['h', 'help', '-h', '--help']):
            print('usage: ./garmin.py <get|build|sync|backup|year|(file)|(directory)|(year(-month(-day)))|(sport)|occur|update>')
            exit(0)
        elif arg == 'get':
            if not os.path.exists('%s/run' % script_path):
                run_command('mkdir -p %s/run/' % script_path)
                os.chdir('%s/run' % script_path)
                run_command('wget --no-check-certificate %s/backup/garmin_data.tar.gz' % BASEURL)
                run_command('tar zxvf garmin_data.tar.gz ; rm garmin_data.tar.gz')
            exit(0)

        if arg == 'sync':
            compare_with_remote(script_path)
            exit(0)

    if not os.path.exists('%s/run' % script_path):
        print('need to download files first')
        exit(0)

    options = {'do_plot': False, 'do_year': False, 'do_month': False, 'do_week': False, 'do_day': False, 'do_file': False, 'do_sport': None, 'do_update': False, 'do_average': False}
    options['script_path'] = script_path
    
    if getattr(args, 'daemon'):
        g = GarminServer()
        g.start_server()
    else:
        garmin_parse_arg_list(getattr(args, 'command'), **options)

if __name__ == '__main__':
    garmin_arg_parse()