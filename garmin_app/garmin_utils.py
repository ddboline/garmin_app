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
from tempfile import NamedTemporaryFile

from .garmin_server import GarminServer
from .util import (run_command, datetimefromstring, openurl,
                   dump_to_file, HOMEDIR, walk_wrapper,
                   OpenPostgreSQLsshTunnel)

BASEURL = 'https://ddbolineathome.mooo.com/~ddboline'
BASEDIR = '%s/setup_files/build/garmin_app' % HOMEDIR
CACHEDIR = '%s/.garmin_cache' % HOMEDIR

if not os.path.exists(CACHEDIR):
    os.makedirs(CACHEDIR)

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
    if '.txt' in gmn_filename.lower():
        return None
    with NamedTemporaryFile(prefix='temp', suffix='.gpx', delete=False) as fn_:
        if '.fit' in gmn_filename.lower():
            tcx_filename = convert_fit_to_tcx(gmn_filename)
            run_command('gpsbabel -i gtrnctr -f %s -o gpx -F %s '
                        % (tcx_filename, fn_.name))
        elif '.tcx' in gmn_filename.lower():
            run_command('gpsbabel -i gtrnctr -f %s -o gpx -F %s'
                        % (gmn_filename, fn_.name))
        else:
            run_command('garmin_gpx %s > %s' % (gmn_filename, fn_.name))
        os.rename(fn_.name, '/tmp/temp.gpx')
        return '/tmp/temp.gpx'

def convert_fit_to_tcx(fit_filename):
    """ fit files to tcx files """
    with NamedTemporaryFile(prefix='temp', suffix='.tcx', delete=False,
                            mode='wt') as fn_:
        if '.fit' in fit_filename.lower():
            if os.path.exists('/usr/bin/fit2tcx'):
                run_command('/usr/bin/fit2tcx -i %s ' % fit_filename +
                            '-o %s 2>&1 > /dev/null' % fn_.name)
            elif os.path.exists('%s/bin/fit2tcx' % os.getenv('HOME')):
                run_command('fit2tcx %s > %s' % (fit_filename, fn_.name))
            elif os.path.exists('./bin/fit2tcx'):
                run_command('./bin/fit2tcx %s > %s' % (fit_filename, fn_.name))
            os.rename(fn_.name, '/tmp/temp.tcx')
            return '/tmp/temp.tcx'
        else:
            return None

def convert_gmn_to_xml(gmn_filename):
    """
        create temporary xml file from gmn,
    """
    if any([a in gmn_filename
            for a in ('.tcx', '.TCX', '.fit', '.FIT', '.xml', '.txt')]):
        return gmn_filename
    with NamedTemporaryFile(prefix='temp', suffix='.xml', delete=False,
                            mode='wt') as xml_file:
        xml_file.write('<root>\n')
        with run_command('garmin_dump %s' % gmn_filename, do_popen=True) as \
                pop_:
            for line in pop_.stdout:
                try:
                    xml_file.write(line)
                except TypeError:
                    xml_file.write(line.decode())
        xml_file.write('</root>\n')
        os.rename(xml_file.name, '/tmp/temp.xml')
        return '/tmp/temp.xml'

def get_md5_old(fname):
    """ md5 function using hashlib.md5 """
    if not os.path.exists(fname):
        return None
    md_ = hashlib.md5()
    with open(fname, 'rb') as infile:
        for line in infile:
            md_.update(line)
    return md_.hexdigest().decode()

def get_md5(fname):
    """ md5 function using cli """
    if not os.path.exists(fname):
        return None
    with run_command('md5sum "%s"' % fname, do_popen=True) as pop_:
        output = pop_.stdout.read().split()[0]
    return output.decode()

def compare_with_remote(cache_dir):
    """ sync files at script_path with files at BASEURL """
    from .save_to_s3 import save_to_s3
    s3_file_chksum = save_to_s3()
    remote_file_chksum = {}
    remote_file_path = {}
    for line in openurl('%s/garmin/files/garmin.list' % BASEURL):
        if len(line) < 2:
            continue
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
            if os.path.isdir(fname) or \
                ('garmin.pkl' in fn_) or \
                ('garmin.list' in fn_) or \
                ('.pkl.gz' in fn_):
                continue
            cmd = 'md5sum %s' % fname
            with run_command(cmd, do_popen=True) as pop_:
                md5sum = pop_.stdout.read().split()[0]
            if fn_ not in local_file_chksum:
                local_file_chksum[fn_] = md5sum

    walk_wrapper('%s/run' % cache_dir, process_files, None)

    for fn_ in remote_file_chksum:
        if fn_ not in local_file_chksum or remote_file_chksum[fn_] != local_file_chksum[fn_]:
            print('download:', fn_, remote_file_chksum[fn_],
                  remote_file_path[fn_], cache_dir)
            if not os.path.exists('%s/run/%s/' % (cache_dir,
                                                  remote_file_path[fn_])):
                os.makedirs('%s/run/%s/' % (cache_dir,
                                            remote_file_path[fn_]))
            with open('%s/run/%s/%s' % (cache_dir, remote_file_path[fn_],
                                        fn_), 'wb') as outfile:
                urlout = '%s/garmin/files/%s/%s' % (BASEURL,
                                                    remote_file_path[fn_],
                                                    fn_)
                dump_to_file(urlout, outfile)

    local_files_not_in_s3 = ['%s/run/%s/%s' % (cache_dir,
                                               remote_file_path[fn_], fn_)
                             for fn_ in local_file_chksum
                             if fn_ not in s3_file_chksum
                             or local_file_chksum[fn_] != s3_file_chksum[fn_]]

    s3_files_not_in_local = [fn_ for fn_ in s3_file_chksum
                             if fn_ not in local_file_chksum
                             or local_file_chksum[fn_] != s3_file_chksum[fn_]]
    if local_files_not_in_s3:
        print('\n'.join(local_files_not_in_s3))
        s3_file_chksum = save_to_s3(filelist=local_files_not_in_s3)
    if s3_files_not_in_local:
        print('missing files', s3_files_not_in_local)
    return

def read_garmin_file(fname, msg_q=None, options=None):
    from .garmin_cache import GarminCache
    from .garmin_report import GarminReport
    from .garmin_parse import GarminParse
    from .garmin_corrections import list_of_corrected_laps
    if options is None:
        options = {'cache_dir': CACHEDIR, 'do_update': False}
    cache_dir = options['cache_dir']

    corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)

    pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
    cache_dir_ = '%s/run/cache' % cache_dir
    cache_ = GarminCache(pickle_file=pickle_file_, cache_directory=cache_dir_,
                         corr_list=corr_list_)
    _temp_file = None
    if not options['do_update']:
        _temp_file = cache_.read_cached_gfile(gfbname=os.path.basename(fname))
    if _temp_file:
        _gfile = _temp_file
    else:
        _gfile = GarminParse(fname, corr_list=corr_list_)
        _gfile.read_file()
    if _gfile:
        cache_.write_cached_gfile(garminfile=_gfile)
    else:
        return False
    _report = GarminReport(cache_obj=cache_, msg_q=msg_q)
    print(_report.file_report_txt(_gfile))
    _report.file_report_html(_gfile, options=options)
    convert_gmn_to_gpx(fname)
    return True

def do_summary(directory_, msg_q=None, options=None):
    from .garmin_cache import GarminCache
    from .garmin_report import GarminReport
    from .garmin_corrections import list_of_corrected_laps
    if options is None:
        options = {'cache_dir': CACHEDIR}
    cache_dir = options['cache_dir']

    corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)

    pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
    cache_dir_ = '%s/run/cache' % cache_dir
    cache_ = GarminCache(pickle_file=pickle_file_, cache_directory=cache_dir_,
                         corr_list=corr_list_)
    if 'build' in options and options['build']:
        summary_list_ = cache_.get_cache_summary_list(directory='%s/run'
                                                      % cache_dir,
                                                      options=options)
        ### backup garmin.pkl.gz info to postgresql database
        with OpenPostgreSQLsshTunnel():
            from .garmin_cache_sql import GarminCacheSQL
            postgre_str = 'postgresql://ddboline:BQGIvkKFZPejrKvX' + \
                          '@localhost:5432/garmin_summary'
            gc_ = GarminCacheSQL(sql_string=postgre_str)
            gc_.delete_table()
            gc_.create_table()
            gc_.write_sql_table(summary_list_)
        return summary_list_


    summary_list_ = cache_.get_cache_summary_list(directory=directory_,
                                                  options=options)
    if not summary_list_:
        return None

    _report = GarminReport(cache_obj=cache_, msg_q=msg_q)
    print(_report.summary_report(summary_list_, options=options))

    return True

def add_correction(correction_str, json_path=None):
    from dateutil.parser import parse
    from .garmin_corrections import (list_of_corrected_laps, save_corrections)
    l_corr = list_of_corrected_laps(json_path=json_path)
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
    l_corr[timestr] = lapdict
    save_corrections(l_corr)
    save_corrections(l_corr, json_path=json_path)
    if os.path.exists('%s/public_html/garmin/files' % HOMEDIR):
        save_corrections(l_corr, json_path='%s/public_html/garmin/files'
                                            % HOMEDIR)
    return l_corr


def garmin_parse_arg_list(args, options=None, msg_q=None):
    if options is None:
        options = {'cache_dir': CACHEDIR}
    cache_dir = options['cache_dir']

    gdir = set()
    for arg in args:
        if arg == 'build':
            if msg_q != None:
                return
            options['build'] = True
        elif arg == 'backup':
            if msg_q != None:
                return
            fname = '%s/garmin_data_%s.tar.gz'\
                     % (cache_dir, datetime.date.today().strftime('%Y%m%d'))
            run_command('cd %s/run/ ; ' % cache_dir +
                        'tar zcvf %s gps_tracks/ garmin.pkl* ' % fname +
                        'garmin_corrections.json cache/')
            if os.path.exists('%s/public_html/backup' % os.getenv('HOME')):
                run_command('cp %s %s/public_html/backup/garmin_data.tar.gz'
                            % (fname, os.getenv('HOME')))
            if os.path.exists('%s/public_html/garmin/tar' % os.getenv('HOME')):
                run_command('mv %s %s/public_html/garmin/tar'
                            % (fname, os.getenv('HOME')))

            from .garmin_cache import GarminCache
            from .garmin_corrections import list_of_corrected_laps

            pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
            cache_dir_ = '%s/run/cache' % cache_dir
            corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)

            cache_ = GarminCache(pickle_file=pickle_file_,
                                 cache_directory=cache_dir_,
                                 corr_list=corr_list_)
            summary_list_ = cache_.cache_read_fn()
            ### backup garmin.pkl.gz info to postgresql database
            with OpenPostgreSQLsshTunnel():
                from .garmin_cache_sql import GarminCacheSQL
                postgre_str = 'postgresql://ddboline:BQGIvkKFZPejrKvX' + \
                              '@localhost:5432/garmin_summary'
                gc_ = GarminCacheSQL(sql_string=postgre_str)
                gc_.delete_table()
                gc_.create_table()
                gc_.write_sql_table(summary_list_)

            return
        elif arg == 'occur':
            options['occur'] = True
        elif os.path.isfile(arg):
            gdir.add(arg)
        elif arg != 'run' and os.path.isdir(arg):
            gdir.add(arg)
        elif arg != 'run' and os.path.isdir('%s/run/%s' % (cache_dir, arg)):
            gdir.add('%s/run/%s' % (cache_dir, arg))
        elif arg == 'correction':
            add_correction(' '.join(args[1:]), json_path='%s/run' % cache_dir)
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
            elif '-' in arg or arg in ('%4d' % _ for _ in range(2008,
                                                datetime.date.today().year+1)):
                files = glob.glob('%s/run/gps_tracks/%s*' % (cache_dir, arg))\
                        + glob.glob('%s/run/gps_tracks/%s*'
                                    % (cache_dir, arg.replace('-', '')))
                basenames = [f.split('/')[-1] for f in sorted(files)]
                if len([x for x in basenames if x[:10] == basenames[0][:10]])\
                        == len(basenames):
                    for fn_ in basenames:
                        print(fn_)
                gdir.update(files)
            elif '.gmn' in arg or 'T' in arg:
                files = glob.glob('%s/run/gps_tracks/%s' % (cache_dir, arg))
                gdir.update(files)
            else:
                print('unhandled argument:', arg)
    if not gdir:
        gdir.add('%s/run/gps_tracks' % cache_dir)

    gdir = sorted(gdir)

    if len(gdir) == 1 and os.path.isfile(gdir[0]):
        return read_garmin_file(gdir[0], msg_q=msg_q, options=options)
    else:
        return do_summary(gdir, msg_q=msg_q, options=options)

def garmin_arg_parse(script_path=BASEDIR, cache_dir=CACHEDIR):
    """ parse command line arguments """
    help_text = 'usage: ./garmin.py <%s>' % '|'.join(COMMANDS)
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('command', nargs='*', help=help_text)
    parser.add_argument('--daemon', '-d', action='store_true',
                        help='run as daemon')
    args = parser.parse_args()

    options = ['build', 'sync', 'backup']

    for arg in getattr(args, 'command'):
        if any(arg == x for x in ['h', 'help', '-h', '--help']):
            print('usage: ./garmin.py <%s>' % '|'.join(COMMANDS))
            return
        elif arg == 'get':
            if not os.path.exists('%s/run' % cache_dir):
                os.makedirs('%s/run/' % cache_dir)
                os.chdir('%s/run' % cache_dir)
                with open('temp.tar.gz', 'wb') as outfile:
                    urlout = '%s/backup/garmin_data.tar.gz' % BASEURL
                    dump_to_file(urlout, outfile)
                if not os.path.exists('temp.tar.gz'):
                    raise OSError
                print('downloaded file')
                run_command('tar zxf temp.tar.gz 2>&1 > /dev/null')
                os.remove('temp.tar.gz')

                from .garmin_cache import (read_pickle_object_in_file as read_,
                                           write_pickle_object_to_file
                                           as write_)

                pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
                summary_list_ = read_(pickle_file=pickle_file_)
                if not summary_list_:
                    with OpenPostgreSQLsshTunnel():
                        from .garmin_cache_sql import GarminCacheSQL
                        postgre_str = 'postgresql://ddboline:BQGIvkKFZPejrKvX' + \
                                      '@localhost:5432/garmin_summary'
                        gc_ = GarminCacheSQL(sql_string=postgre_str)
                        summary_list_ = gc_.read_sql_table()
                        print(len(summary_list_), pickle_file_)
                        print(summary_list_[0])
                        write_(summary_list_, pickle_file_)
            return

        if arg == 'sync':
            compare_with_remote(cache_dir)
            return

    if not os.path.exists('%s/run' % cache_dir):
        print('need to download files first')
        return

    options = {'do_plot': False, 'do_year': False, 'do_month': False,
               'do_week': False, 'do_day': False, 'do_file': False,
               'do_sport': None, 'do_update': False, 'do_average': False}
    options['script_path'] = script_path
    options['cache_dir'] = cache_dir

    if getattr(args, 'daemon'):
        with GarminServer() as gar:
            return gar
    else:
        return garmin_parse_arg_list(getattr(args, 'command'), options=options)
