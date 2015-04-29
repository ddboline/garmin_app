#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Main module
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
#import glob
import argparse

import ssl
from urllib2 import urlopen

#from garmin_app.garmin_cache import GarminCache
#from garmin_app.garmin_parse import GarminParse
#from garmin_app.garmin_report import GarminReport
from garmin_app.garmin_utils import compare_with_remote,\
     garmin_parse_arg_list, BASEURL
from garmin_app.garmin_daemon import GarminServer

from garmin_app.util import run_command

def garmin_arg_parse():
    """ parse command line arguments """
    commands = ['get', 'build', 'sync', 'backup', 'year', '(file)',
                '(directory)', '(year(-month(-day)))', '(sport)', 'occur',
                'update']
    help_text = 'usage: ./garmin.py <%s>' % '|'.join(commands)
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('command', nargs='*', help=help_text)
    parser.add_argument('--daemon', '-d', action='store_true',
                        help='run as daemon')
    args = parser.parse_args()

    options = ['build', 'sync', 'backup']

    #print(os.sys.argv)
    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])

    if '%s/bin' % script_path not in os.getenv('PATH'):
        os.putenv('PATH', '%s:%s/bin' % (os.getenv('PATH'), script_path))

    for arg in getattr(args, 'command'):
        if any(arg == x for x in ['h', 'help', '-h', '--help']):
            print('usage: ./garmin.py <%s>' % '|'.join(commands))
            exit(0)
        elif arg == 'get':
            if not os.path.exists('%s/run' % script_path):
                os.makedirs('%s/run/' % script_path)
                os.chdir('%s/run' % script_path)
                outfile = open('temp.tar.gz', 'wb')
                gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                urlout = urlopen('%s/backup/garmin_data.tar.gz' % BASEURL, context=gcontext)
                if urlout.getcode() != 200:
                    print('something bad happened %d' % urlout.getcode())
                    exit(0)
                for line in urlout:
                    outfile.write(line)
                outfile.close()
                print('downloaded file')
                run_command('tar zxf temp.tar.gz 2>&1 > /dev/null')
                os.remove('temp.tar.gz')
            exit(0)

        if arg == 'sync':
            compare_with_remote(script_path)
            exit(0)

    if not os.path.exists('%s/run' % script_path):
        print('need to download files first')
        exit(0)

    options = {'do_plot': False, 'do_year': False, 'do_month': False,
               'do_week': False, 'do_day': False, 'do_file': False,
               'do_sport': None, 'do_update': False, 'do_average': False}
    options['script_path'] = script_path

    if getattr(args, 'daemon'):
        gar = GarminServer()
        gar.start_server()
    else:
        garmin_parse_arg_list(getattr(args, 'command'), **options)

if __name__ == '__main__':
    garmin_arg_parse()
