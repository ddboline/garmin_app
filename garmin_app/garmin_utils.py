#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    Utility functions to convert:
        gmn to gpx
        gmn to xml
        fit to tcx
'''

import os

try:
    from util import run_command, datetimefromstring
except ImportError:
    if os.path.exists('%s/scripts' % os.getenv('HOME')):
        os.sys.path.append('%s/scripts' % os.getenv('HOME'))
        from util import run_command, datetimefromstring

### Useful constants
METERS_PER_MILE = 1609.344 # meters
MARATHON_DISTANCE_M = 42195 # meters
MARATHON_DISTANCE_MI = MARATHON_DISTANCE_M / METERS_PER_MILE # meters

### explicitly specify available types...
SPORT_TYPES = ('running', 'biking', 'walking', 'ultimate', 'elliptical', 'stairs', 'lifting', 'swimming', 'other', 'snowshoeing', 'skiing')
MONTH_NAMES = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
WEEKDAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

### maybe change output to datetime object?
def convert_date_string(date_str):
    ''' convert date string to datetime object '''
    return datetimefromstring(date_str, ignore_tz=True)

def expected_calories(weight=175, pace_min_per_mile=10.0, distance=1.0):
    ''' return expected calories for running at a given pace '''
    cal_per_mi = weight * (0.0395 + 0.00327 * (60./pace_min_per_mile) + 0.000455 * (60./pace_min_per_mile)**2 + 0.000801 * (weight/154) * 0.425 / weight * (60./pace_min_per_mile)**3) * 60. / (60./pace_min_per_mile)
    return cal_per_mi * distance

def print_date_string(d):
    ''' datetime object to standardized string '''
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')

def convert_time_string(time_str):
    ''' time string to seconds '''
    hour = int(time_str.split(':')[0])
    minute = int(time_str.split(':')[1])
    second = float(time_str.split(':')[2])
    return second + 60*(minute + 60 * (hour))

def print_h_m_s(second, do_hours=True):
    ''' seconds to hh:mm:ss string '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    if hours > 0:
        return '%02i:%02i:%02i' % (hours, minutes, seconds)
    elif hours == 0:
        if do_hours:
            return '00:%02i:%02i' % (minutes, seconds)
        else:
            return '%02i:%02i' % (minutes, seconds)


def convert_gmn_to_gpx(gmn_filename):
    ''' create temporary gpx file from gmn or tcx files '''
    if '.fit' in gmn_filename.lower():
        tcx_filename = convert_fit_to_tcx(gmn_filename)
        run_command('gpsbabel -i gtrnctr -f %s -o gpx -F /tmp/temp.gpx '
            % (tcx_filename))
    elif '.tcx' in gmn_filename.lower():
        run_command('gpsbabel -i gtrnctr -f %s -o gpx -F /tmp/temp.gpx'
            % gmn_filename)
    elif '.txt' in gmn_filename.lower():
        return None
    else:
        run_command('garmin_gpx %s > /tmp/temp.gpx' % gmn_filename)
    return '/tmp/temp.gpx'

def convert_fit_to_tcx(fit_filename):
    ''' fit files to tcx files '''
    if '.fit' in fit_filename.lower():
        if os.path.exists('%s/bin/fit2tcx' % os.getenv('HOME')):
            run_command('fit2tcx %s > /tmp/temp.tcx' % fit_filename)
        elif os.path.exists('./bin/fit2tcx'):
            run_command('./bin/fit2tcx %s > /tmp/temp.tcx' % fit_filename)
    else:
        return False
    return '/tmp/temp.tcx'

def convert_gmn_to_xml(gmn_filename):
    '''
        create temporary xml file from gmn,
    '''
    if any([a in gmn_filename
            for a in ('.tcx', '.TCX', '.fit', '.FIT', '.xml', '.txt')]):
        return gmn_filename
    with open('/tmp/.temp.xml', 'w') as xml_file:
        xml_file.write('<root>\n')
        for line in run_command('garmin_dump %s' % gmn_filename, do_popen=True):
            xml_file.write(line)
        xml_file.write('</root>\n')
    run_command('mv /tmp/.temp.xml /tmp/temp.xml')
    return '/tmp/temp.xml'

def get_md5_full(fname):
    if not os.path.exists(fname):
        return None
    m = hashlib.md5()
    with open(fname, 'r') as infile:
        for line in infile:
            m.update(line)
    return m.hexdigest()
