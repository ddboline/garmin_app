#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    Utility functions to convert:
        gmn to gpx
        gmn to xml
        fit to tcx
'''

import os
import glob
import hashlib
import datetime

try:
    from util import run_command, datetimefromstring
except ImportError:
    if os.path.exists('%s/scripts' % os.getenv('HOME')):
        os.sys.path.append('%s/scripts' % os.getenv('HOME'))
        from util import run_command, datetimefromstring

BASEURL = 'https://ddbolineathome.mooo.com/~ddboline'

### Useful constants
METERS_PER_MILE = 1609.344 # meters
MARATHON_DISTANCE_M = 42195 # meters
MARATHON_DISTANCE_MI = MARATHON_DISTANCE_M / METERS_PER_MILE # meters

### explicitly specify available types...
SPORT_TYPES = ('running', 'biking', 'walking', 'ultimate', 'elliptical', 'stairs', 'lifting', 'swimming', 'other', 'snowshoeing', 'skiing')
MONTH_NAMES = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
WEEKDAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

def days_in_year(year=datetime.date.today().year):
    ''' return number of days in a given year '''
    return (datetime.date(year=year+1, month=1, day=1)-datetime.date(year=year, month=1, day=1)).days

def days_in_month(month=datetime.date.today().month, year=datetime.date.today().year):
    ''' return number of days in a given month '''
    y1, m1 = year, month + 1
    if m1 == 13:
        y1, m1 = y1 + 1, 1
    return (datetime.date(year=y1, month=m1, day=1)-datetime.date(year=year, month=month, day=1)).days

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

def compare_with_remote(script_path):
    from urllib2 import urlopen
    from garmin_app import save_to_s3
    s3_file_chksum = save_to_s3.save_to_s3()
    remote_file_chksum = {}
    remote_file_path = {}
    for line in urlopen('%s/garmin/files/garmin.list' % BASEURL):
        md5sum, fname = line.split()[0:2]
        fn = fname.split('/')[-1]
        if fn not in remote_file_chksum:
            remote_file_chksum[fn] = md5sum
            remote_file_path[fn] = '/'.join(fname.split('/')[:-1])
        else:
            print('duplicate?:', fname, md5sum, remote_file_chksum[fn])

    local_file_chksum = {}

    def process_files(arg, dirname, names):
        for fn in names:
            fname = '%s/%s' % (dirname, fn)
            if os.path.isdir(fname) or fn == 'garmin.pkl' or fn == 'garmin.list':
                continue
            cmd = 'md5sum %s' % fname
            md5sum = run_command(cmd, do_popen=True).read().split()[0]
            if fn not in local_file_chksum:
                local_file_chksum[fn] = md5sum

    os.path.walk('%s/run' % script_path, process_files, None)

    for fn in remote_file_chksum.keys():
        if fn not in local_file_chksum.keys():
            print('download:', fn, remote_file_chksum[fn], remote_file_path[fn], script_path)
            if not os.path.exists('%s/run/%s/' % (script_path, remote_file_path[fn])):
                os.makedirs('%s/run/%s/' % (script_path, remote_file_path[fn]))
            if not os.path.exists('%s/run/%s/%s' % (script_path, remote_file_path[fn], fn)):
                outfile = open('%s/run/%s/%s' % (script_path, remote_file_path[fn], fn), 'wb')
                urlout = urlopen('%s/garmin/files/%s/%s' % (BASEURL, remote_file_path[fn], fn))
                if urlout.getcode() != 200:
                    print('something bad happened %d' % urlout.getcode())
                    exit(0)
                for line in urlout:
                    outfile.write(line)
                outfile.close()
    
    local_files_not_in_s3 = ['%s/run/%s/%s' % (script_path, remote_file_path[fn], fn)
                             for fn in local_file_chksum
                             if fn not in s3_file_chksum]

    s3_files_not_in_local = [fn for fn in s3_file_chksum if fn not in local_file_chksum]
    if local_files_not_in_s3:
        print('\n'.join(local_files_not_in_s3))
        s3_file_chksum = save_to_s3.save_to_s3(filelist=local_files_not_in_s3)
    if s3_files_not_in_local:
        print('missing files', s3_files_not_in_local)
    return

def read_garmin_file(fname, **options):
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_report import GarminReport
    script_path = options['script_path']
    _pickle_file = '%s/run/garmin.pkl.gz' % script_path
    _cache_dir = '%s/cache' % script_path
    _cache = GarminCache(pickle_file=_pickle_file, cache_directory=_cache_dir)
    _temp_file = _cache.read_cached_gfile(gfbasename=os.path.basename(fname))
    if _temp_file:
        _gfile = _temp_file
    else:
        _gfile = GarminParse(fname)
        _gfile.read_file()
    if _gfile:
        _cache.write_cached_gfile(garminfile=_gfile)
    else:
        return False
    _report = GarminReport(cache_obj=_cache)
    print(_report.file_report_txt(_gfile))
    _report.file_report_html(_gfile, **options)
    return True

def do_summary(directory_, **options):
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_report import GarminReport
    script_path = options['script_path']
    _pickle_file = '%s/run/garmin.pkl.gz' % script_path
    _cache_dir = '%s/cache' % script_path
    _cache = GarminCache(pickle_file=_pickle_file, cache_directory=_cache_dir)
    if 'build' in options and options['build']:
        return _cache.get_cache_summary_list(directory='%s/run' % script_path)
    _summary_list = _cache.get_cache_summary_list(directory=directory_)
    if not _summary_list:
        return None
    _report = GarminReport(cache_obj=_cache)
    _report.summary_report(_summary_list, **options)

def garmin_parse_arg_list(args, **options):
    script_path = options['script_path']

    gdir = []
    for arg in args:
        if arg == 'build':
            options['build'] = True
        elif arg == 'backup':
            fname = '%s/garmin_data_%s.tar.gz' % (script_path, datetime.date.today().strftime('%Y%m%d'))
            run_command('cd %s/run/ ; tar zcvf %s 2* garmin.pkl' % (script_path, fname))
            if os.path.exists('%s/public_html/backup' % os.getenv('HOME')):
                run_command('cp %s %s/public_html/backup/garmin_data.tar.gz' % (fname, os.getenv('HOME')))
            if os.path.exists('%s/public_html/garmin/tar' % os.getenv('HOME')):
                run_command('mv %s %s/public_html/garmin/tar' % (fname, os.getenv('HOME')))
            exit(0)
        elif arg == 'occur':
            options['occur'] = True
        elif os.path.isfile(arg):
            gdir.append(arg)
            # read_garmin_file(arg)
            # exit(0)
        elif arg != 'run' and os.path.isdir(arg):
            gdir.append(arg)
        elif arg != 'run' and os.path.isdir('%s/run/%s' % (script_path, arg)):
            gdir.append('%s/run/%s' % (script_path, arg))
        elif arg in options:
            options[arg] = True
        elif 'do_%s' % arg in options:
            options['do_%s' % arg] = True
        else:
            spts = filter(lambda x: arg in x, list(SPORT_TYPES))
            if len(spts) > 0:
                options['do_sport'] = spts[0]
            elif arg == 'bike':
                options['do_sport'] = 'biking'
            elif '-' in arg:
                ent = arg.split('-')
                year = ent[0]
                if len(ent) > 1:
                    month = ent[1]
                else:
                    month = '*'
                files = glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, arg)) + glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, ''.join(ent)))
                basenames = [f.split('/')[-1] for f in sorted(files)]
                if len(filter(lambda x: x[:10] == basenames[0][:10], basenames)) == len(basenames):
                    for f in basenames:
                        print(f)
                gdir += files
            elif '.gmn' in arg or 'T' in arg:
                files = glob.glob('%s/run/*/*/%s' % (script_path, arg))
                gdir += files
            else:
                print('unhandled argument:',arg)
    if not gdir:
        gdir.append('%s/run' % script_path)

    
    if len(gdir) == 1 and os.path.isfile(gdir[0]):
        read_garmin_file(gdir[0], **options)
    else:
        do_summary(gdir, **options)
