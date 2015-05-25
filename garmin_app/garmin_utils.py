# -*- coding: utf-8 -*-
"""
    Utility functions to convert:
        gmn to gpx
        gmn to xml
        fit to tcx
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import glob
import hashlib
import datetime
import argparse

import garmin_app
from garmin_app.garmin_daemon import GarminServer
from garmin_app.util import run_command, datetimefromstring, openurl, HOMEDIR

BASEURL = 'https://ddbolineathome.mooo.com/~ddboline'
BASEDIR = '%s/setup_files/build/garmin_app' % HOMEDIR

if not os.path.exists(BASEDIR):
    BASEDIR = os.path.abspath('../%s' % garmin_app.__path__[0])

### Useful constants
METERS_PER_MILE = 1609.344 # meters
MARATHON_DISTANCE_M = 42195 # meters
MARATHON_DISTANCE_MI = MARATHON_DISTANCE_M / METERS_PER_MILE # meters

### explicitly specify available types...
SPORT_TYPES = ('running', 'biking', 'walking', 'ultimate', 'elliptical',
               'stairs', 'lifting', 'swimming', 'other', 'snowshoeing',
               'skiing')
MONTH_NAMES = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
               'Oct', 'Nov', 'Dec')
WEEKDAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

COMMANDS = ('get', 'build', 'sync', 'backup', 'year', '(file)', '(directory)',
            '(year(-month(-day)))', '(sport)', 'occur', 'update', 'correction')


def days_in_year(year=datetime.date.today().year):
    """ return number of days in a given year """
    return (datetime.date(year=year+1, month=1, day=1)
            - datetime.date(year=year, month=1, day=1)).days

def days_in_month(month=None, year=None):
    """ return number of days in a given month """
    if not month:
        month = datetime.date.today().month
    if not year:
        year = datetime.date.today().year
    y1_, m1_ = year, month + 1
    if m1_ == 13:
        y1_, m1_ = y1_ + 1, 1
    return (datetime.date(year=y1_, month=m1_, day=1)
            - datetime.date(year=year, month=month, day=1)).days

### maybe change output to datetime object?
def convert_date_string(date_str, ignore_tz=True):
    """ convert date string to datetime object """
    return datetimefromstring(date_str, ignore_tz=ignore_tz)

def expected_calories(weight=175, pace_min_per_mile=10.0, distance=1.0):
    """ return expected calories for running at a given pace """
    cal_per_mi = weight * (0.0395 + 0.00327 * (60./pace_min_per_mile)
                           + 0.000455 * (60./pace_min_per_mile)**2
                           + 0.000801 * ((weight/154) * 0.425 / weight
                                         * (60./pace_min_per_mile)**3)
                                         * 60. / (60./pace_min_per_mile))
    return cal_per_mi * distance

def print_date_string(dt_):
    """ datetime object to standardized string """
    return dt_.strftime('%Y-%m-%dT%H:%M:%SZ')

def convert_time_string(time_str):
    """ time string to seconds """
    hour = int(time_str.split(':')[0])
    minute = int(time_str.split(':')[1])
    second = float(time_str.split(':')[2])
    return second + 60*(minute + 60 * (hour))

def print_h_m_s(second, do_hours=True):
    """ seconds to hh:mm:ss string """
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
    """ create temporary gpx file from gmn or tcx files """
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
    """ fit files to tcx files """
    if '.fit' in fit_filename.lower():
        if os.path.exists('%s/bin/fit2tcx' % os.getenv('HOME')):
            run_command('fit2tcx %s > /tmp/temp.tcx' % fit_filename)
        elif os.path.exists('./bin/fit2tcx'):
            run_command('./bin/fit2tcx %s > /tmp/temp.tcx' % fit_filename)
    else:
        return False
    return '/tmp/temp.tcx'

def convert_gmn_to_xml(gmn_filename):
    """
        create temporary xml file from gmn,
    """
    if any([a in gmn_filename
            for a in ('.tcx', '.TCX', '.fit', '.FIT', '.xml', '.txt')]):
        return gmn_filename
    with open('/tmp/.temp.xml', 'w') as xml_file:
        xml_file.write('<root>\n')
        for line in run_command('garmin_dump %s' % gmn_filename,
                                do_popen=True):
            xml_file.write(line)
        xml_file.write('</root>\n')
    run_command('mv /tmp/.temp.xml /tmp/temp.xml')
    return '/tmp/temp.xml'

def get_md5_old(fname):
    """ md5 function using hashlib.md5 """
    if not os.path.exists(fname):
        return None
    md_ = hashlib.md5()
    with open(fname, 'r') as infile:
        for line in infile:
            md_.update(line)
    return md_.hexdigest()

def get_md5(fname):
    """ md5 function using cli """
    if not os.path.exists(fname):
        return None
    output = run_command('md5sum "%s"' % fname,
                         do_popen=True).read().split()[0]
    return output

def compare_with_remote(script_path):
    """ sync files at script_path with files at BASEURL """
    from garmin_app import save_to_s3
    s3_file_chksum = save_to_s3.save_to_s3()
    remote_file_chksum = {}
    remote_file_path = {}
    for line in openurl('%s/garmin/files/garmin.list' % BASEURL):
        md5sum, fname = line.split()[0:2]
        fn_ = fname.split('/')[-1]
        if fn_ not in remote_file_chksum:
            remote_file_chksum[fn_] = md5sum
            remote_file_path[fn_] = '/'.join(fname.split('/')[:-1])
        else:
            print('duplicate?:', fname, md5sum, remote_file_chksum[fn_])

    local_file_chksum = {}

    def process_files(_, dirname, names):
        """ callback function for os.walk """
        for fn_ in names:
            fname = '%s/%s' % (dirname, fn_)
            if os.path.isdir(fname) or\
                ('garmin.pkl' in fn_) or\
                ('garmin.list' in fn_) or\
                ('.pkl.gz' in fn_):
                continue
            cmd = 'md5sum %s' % fname
            md5sum = run_command(cmd, do_popen=True).read().split()[0]
            if fn_ not in local_file_chksum:
                local_file_chksum[fn_] = md5sum

    os.path.walk('%s/run' % script_path, process_files, None)

    for fn_ in remote_file_chksum.keys():
        if fn_ not in local_file_chksum.keys():
            print('download:', fn_, remote_file_chksum[fn_],
                  remote_file_path[fn_], script_path)
            if not os.path.exists('%s/run/%s/' % (script_path,
                                                  remote_file_path[fn_])):
                os.makedirs('%s/run/%s/' % (script_path,
                                            remote_file_path[fn_]))
            if not os.path.exists('%s/run/%s/%s' % (script_path,
                                                    remote_file_path[fn_],
                                                    fn_)):
                outfile = open('%s/run/%s/%s' % (script_path,
                                                 remote_file_path[fn_],
                                                 fn_), 'wb')
                urlout = openurl('%s/garmin/files/%s/%s'
                                 % (BASEURL, remote_file_path[fn_], fn_))
                if urlout.getcode() != 200:
                    print('something bad happened %d' % urlout.getcode())
                    from urllib2 import HTTPError
                    raise HTTPError
                for line in urlout:
                    outfile.write(line)
                urlout.close()
                outfile.close()

    local_files_not_in_s3 = ['%s/run/%s/%s' % (script_path,
                                               remote_file_path[fn_], fn_)
                             for fn_ in local_file_chksum
                             if fn_ not in s3_file_chksum]

    s3_files_not_in_local = [fn_ for fn_ in s3_file_chksum
                             if fn_ not in local_file_chksum]
    if local_files_not_in_s3:
        print('\n'.join(local_files_not_in_s3))
        s3_file_chksum = save_to_s3.save_to_s3(filelist=local_files_not_in_s3)
    if s3_files_not_in_local:
        print('missing files', s3_files_not_in_local)
    return

def read_garmin_file(fname, msg_q=None, **options):
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_report import GarminReport
    from garmin_app.garmin_parse import GarminParse
    script_path = options['script_path']
    _pickle_file = '%s/run/garmin.pkl.gz' % script_path
    _cache_dir = '%s/run/cache' % script_path
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
    _report = GarminReport(cache_obj=_cache, msg_q=msg_q)
    print(_report.file_report_txt(_gfile))
    _report.file_report_html(_gfile, **options)
    convert_gmn_to_gpx(fname)
    return True

def do_summary(directory_, msg_q=None, **options):
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_report import GarminReport
    script_path = options['script_path']
    _pickle_file = '%s/run/garmin.pkl.gz' % script_path
    _cache_dir = '%s/run/cache' % script_path
    _cache = GarminCache(pickle_file=_pickle_file, cache_directory=_cache_dir)
    if 'build' in options and options['build']:
        return _cache.get_cache_summary_list(directory='%s/run' % script_path,
                                             **options)
    _summary_list = _cache.get_cache_summary_list(directory=directory_,
                                                  **options)
    if not _summary_list:
        return None
    _report = GarminReport(cache_obj=_cache, msg_q=msg_q)
    print(_report.summary_report(_summary_list, **options))
    return True

def add_correction(correction_str):
    from dateutil.parser import parse
    from garmin_app.garmin_corrections import list_of_corrected_laps,\
                                              save_corrections

    ent = correction_str.split()
    timestr = ent[0]
    try:
        parse(timestr)
    except ValueError:
        return
    lapdict = {}
    for idx, line in enumerate(ent[1:]):
        ent = line.split()
        tmp_ = []
        if len(ent) == 0:
            continue
        if len(ent) > 0:
            try:
                lapdist = float(ent[0])
            except ValueError:
                continue
            tmp_.append(lapdist)
        if len(ent) > 1:
            try:
                laptime = float(ent[1])
            except ValueError:
                laptime = None
            tmp_.append(laptime)
        if len(tmp_) == 1:
            lapdict[idx] = tmp_[0]
        elif len(tmp_) > 1:
            lapdict[idx] = tmp_
    list_of_corrected_laps[timestr] = lapdict
    save_corrections(list_of_corrected_laps)
    return list_of_corrected_laps


def garmin_parse_arg_list(args, msg_q=None, **options):
    script_path = options['script_path']

    gdir = []
    for arg in args:
        if arg == 'build':
            if msg_q != None:
                return
            options['build'] = True
        elif arg == 'backup':
            if msg_q != None:
                return
            fname = '%s/garmin_data_%s.tar.gz'\
                     % (script_path, datetime.date.today().strftime('%Y%m%d'))
            run_command('cd %s/run/ ; tar zcvf %s 2* garmin.pkl* cache/'
                        % (script_path, fname))
            if os.path.exists('%s/public_html/backup' % os.getenv('HOME')):
                run_command('cp %s %s/public_html/backup/garmin_data.tar.gz'
                             % (fname, os.getenv('HOME')))
            if os.path.exists('%s/public_html/garmin/tar' % os.getenv('HOME')):
                run_command('mv %s %s/public_html/garmin/tar'
                             % (fname, os.getenv('HOME')))
            return
        elif arg == 'occur':
            options['occur'] = True
        elif os.path.isfile(arg):
            gdir.append(arg)
        elif arg != 'run' and os.path.isdir(arg):
            gdir.append(arg)
        elif arg != 'run' and os.path.isdir('%s/run/%s' % (script_path, arg)):
            gdir.append('%s/run/%s' % (script_path, arg))
        elif arg == 'correction':
            add_correction(' '.join(args[1:]))
            exit(0)
        elif arg in options:
            options[arg] = True
        elif 'do_%s' % arg in options:
            options['do_%s' % arg] = True
        else:
            spts = [x for x in SPORT_TYPES if arg in x]
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
                files = glob.glob('%s/run/%s/%s/%s*' % (script_path, year,
                                                        month, arg))\
                        + glob.glob('%s/run/%s/%s/%s*' % (script_path, year,
                                                          month, ''.join(ent)))
                basenames = [f.split('/')[-1] for f in sorted(files)]
                if len([x for x in basenames if x[:10] == basenames[0][:10]])\
                        == len(basenames):
                    for fn_ in basenames:
                        print(fn_)
                gdir += files
            elif '.gmn' in arg or 'T' in arg:
                files = glob.glob('%s/run/*/*/%s' % (script_path, arg))
                gdir += files
            else:
                print('unhandled argument:', arg)
    if not gdir:
        gdir.append('%s/run' % script_path)

    if len(gdir) == 1 and os.path.isfile(gdir[0]):
        return read_garmin_file(gdir[0], msg_q, **options)
    else:
        return do_summary(gdir, msg_q, **options)

def garmin_arg_parse():
    """ parse command line arguments """
    help_text = 'usage: ./garmin.py <%s>' % '|'.join(COMMANDS)
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('command', nargs='*', help=help_text)
    parser.add_argument('--daemon', '-d', action='store_true',
                        help='run as daemon')
    args = parser.parse_args()

    options = ['build', 'sync', 'backup']

    #print(os.sys.argv)
    script_path = BASEDIR
    if not os.path.exists(script_path):
        script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])


    if '%s/bin' % script_path not in os.getenv('PATH'):
        os.putenv('PATH', '%s:%s/bin' % (os.getenv('PATH'), script_path))

    for arg in getattr(args, 'command'):
        if any(arg == x for x in ['h', 'help', '-h', '--help']):
            print('usage: ./garmin.py <%s>' % '|'.join(COMMANDS))
            return
        elif arg == 'get':
            if not os.path.exists('%s/run' % script_path):
                os.makedirs('%s/run/' % script_path)
                os.chdir('%s/run' % script_path)
                outfile = open('temp.tar.gz', 'wb')
                urlout = openurl('%s/backup/garmin_data.tar.gz' % BASEURL)
                if urlout.getcode() != 200:
                    print('something bad happened %d' % urlout.getcode())
                    from urllib2 import HTTPError
                    raise HTTPError
                for line in urlout:
                    outfile.write(line)
                outfile.close()
                print('downloaded file')
                run_command('tar zxf temp.tar.gz 2>&1 > /dev/null')
                os.remove('temp.tar.gz')
            return

        if arg == 'sync':
            compare_with_remote(script_path)
            return

    if not os.path.exists('%s/run' % script_path):
        print('need to download files first')
        return

    options = {'do_plot': False, 'do_year': False, 'do_month': False,
               'do_week': False, 'do_day': False, 'do_file': False,
               'do_sport': None, 'do_update': False, 'do_average': False}
    options['script_path'] = script_path

    if getattr(args, 'daemon'):
        gar = GarminServer()
        gar.start_server()
    else:
        garmin_parse_arg_list(getattr(args, 'command'), **options)
