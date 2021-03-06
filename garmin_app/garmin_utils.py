# -*- coding: utf-8 -*-
"""
    Utility functions to convert:
        gmn to gpx
        gmn to xml
        fit to tcx
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
from dateutil.parser import parse
import glob
import hashlib
import datetime
import argparse
from tempfile import NamedTemporaryFile

from garmin_app.garmin_server import garmin_server
from garmin_app.save_to_s3 import get_list_of_keys, download_from_s3
from garmin_app.util import (run_command, dump_to_file, HOMEDIR, walk_wrapper, datetimefromstring,
                             HOSTNAME)

# 'https://home.ddboline.net/~ddboline'
BASEURL = 'http://cloud.ddboline.net/~ubuntu'
BASEDIR = '%s/setup_files/build/garmin_app' % HOMEDIR
CACHEDIR = '%s/.garmin_cache' % HOMEDIR

if not os.path.exists(CACHEDIR):
    os.makedirs(CACHEDIR)

# Useful constants
METERS_PER_MILE = 1609.344  # meters
MARATHON_DISTANCE_M = 42195  # meters
MARATHON_DISTANCE_MI = MARATHON_DISTANCE_M / METERS_PER_MILE  # meters

# explicitly specify available types...
SPORT_TYPES = ('running', 'biking', 'walking', 'ultimate', 'elliptical', 'stairs', 'lifting',
               'swimming', 'other', 'snowshoeing', 'skiing')
SPORT_MAP = {k: k for k in SPORT_TYPES}
for o, n in ('running', 'run'), ('biking', 'bike'):
    SPORT_MAP[o] = n
MONTH_NAMES = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
WEEKDAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

COMMANDS = ('get', 'build', 'sync', 'backup', 'year', '(file)', '(directory)',
            '(year(-month(-day)))', '(sport)', 'occur', 'update', 'correction', 'check')


def days_in_year(year=datetime.date.today().year):
    """ return number of days in a given year """
    return (datetime.date(year=year + 1, month=1, day=1) - datetime.date(year=year, month=1,
                                                                         day=1)).days


def days_in_month(month=None, year=None):
    """ return number of days in a given month """
    if not month:
        month = datetime.date.today().month
    if not year:
        year = datetime.date.today().year
    y1_, m1_ = year, month + 1
    if m1_ == 13:
        y1_, m1_ = y1_ + 1, 1
    return (datetime.date(year=y1_, month=m1_, day=1) - datetime.date(
        year=year, month=month, day=1)).days


def expected_calories(weight=175, pace_min_per_mile=10.0, distance=1.0):
    """ return expected calories for running at a given pace """
    cal_per_mi = weight * (0.0395 + 0.00327 * (60. / pace_min_per_mile) + 0.000455 *
                           (60. / pace_min_per_mile)**2 + 0.000801 * (
                               (weight / 154) * 0.425 / weight *
                               (60. / pace_min_per_mile)**3) * 60. / (60. / pace_min_per_mile))
    return cal_per_mi * distance


def print_date_string(dt_):
    """ datetime object to standardized string """
    return dt_.strftime('%Y-%m-%dT%H:%M:%SZ')


def convert_date_string(date_str, ignore_tz=True):
    """ wrapper around garmin_app.util.datetimefromstring """
    return datetimefromstring(date_str, ignore_tz=ignore_tz)


def convert_time_string(time_str):
    """ time string to seconds """
    hour = int(time_str.split(':')[0])
    minute = int(time_str.split(':')[1])
    second = float(time_str.split(':')[2])
    return second + 60 * (minute + 60 * (hour))


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
            run_command('gpsbabel -i gtrnctr -f %s -o gpx -F %s ' % (tcx_filename, fn_.name))
            os.remove(tcx_filename)
        elif '.tcx' in gmn_filename.lower():
            run_command('gpsbabel -i gtrnctr -f %s -o gpx -F %s' % (gmn_filename, fn_.name))
        else:
            run_command('garmin_gpx %s > %s' % (gmn_filename, fn_.name))
        return fn_.name


def convert_fit_to_tcx(fit_filename):
    """ fit files to tcx files """
    with NamedTemporaryFile(prefix='temp', suffix='.tcx', delete=False, mode='wt') as fn_:
        if '.fit' in fit_filename.lower():
            if os.path.exists('/usr/bin/fit2tcx'):
                run_command('/usr/bin/fit2tcx -i %s ' % fit_filename +
                            '-o %s 2>&1 > /dev/null' % fn_.name)
            elif os.path.exists('%s/bin/fit2tcx' % os.getenv('HOME')):
                run_command('fit2tcx %s > %s' % (fit_filename, fn_.name))
            elif os.path.exists('./bin/fit2tcx'):
                run_command('./bin/fit2tcx %s > %s' % (fit_filename, fn_.name))
            return fn_.name
        else:
            os.remove(fn_.name)
            return None


def convert_gmn_to_xml(gmn_filename):
    """
        create temporary xml file from gmn,
    """
    if any([a in gmn_filename for a in ('.tcx', '.TCX', '.fit', '.FIT', '.xml', '.txt')]):
        return gmn_filename
    with NamedTemporaryFile(prefix='temp', suffix='.xml', delete=False, mode='wt') as xml_file:
        xml_file.write('<root>\n')
        with run_command('garmin_dump %s' % gmn_filename, do_popen=True) as \
                pop_:
            for line in pop_:
                if hasattr(line, 'decode'):
                    line = line.decode()
                xml_file.write(line)
        xml_file.write('</root>\n')
        return xml_file.name


def get_md5_old(fname):
    """ md5 function using hashlib.md5 """
    if not os.path.exists(fname):
        return None
    md_ = hashlib.md5()
    with open(fname, 'rb') as infile:
        for line in infile:
            md_.update(line)
    output = md_.hexdigest()
    if hasattr(output, 'decode'):
        output = output.decode()
    return output


def get_md5(fname):
    """ md5 function using cli """
    if not os.path.exists(fname):
        return None
    output = run_command('md5sum "%s"' % fname, do_popen=True, single_line=True).split()[0]
    return output.decode()


def sync_db(to_local=True, to_remote=False):
    from garmin_app.garmin_cache_sql import (read_postgresql_table, write_postgresql_table)
    from garmin_app.garmin_corrections_sql import (read_corrections_table, write_corrections_table)

    if HOSTNAME in ('dilepton-tower', 'dilepton-chromebook'):
        return
    cache_local = read_postgresql_table(do_tunnel=False)
    cache_remote = read_postgresql_table(do_tunnel=True)

    if to_local:
        summary_list = {}
        summary_list.update(cache_local)
        summary_list.update(cache_remote)
        write_postgresql_table(summary_list, do_tunnel=False)

    if to_remote:
        summary_list = {}
        summary_list.update(cache_remote)
        summary_list.update(cache_local)
        write_postgresql_table(summary_list, do_tunnel=True)

    corrections_local = read_corrections_table(do_tunnel=False)
    corrections_remote = read_corrections_table(do_tunnel=True)

    if to_local:
        corrections = {}
        corrections.update(corrections_local)
        corrections.update(corrections_remote)
        write_corrections_table(corrections, do_tunnel=False)

    if to_remote:
        corrections = {}
        corrections.update(corrections_remote)
        corrections.update(corrections_local)
        write_corrections_table(corrections, do_tunnel=True)


def compare_with_remote(cache_dir, sync_cache=False):
    """ sync files at script_path with files at BASEURL """
    from garmin_app.save_to_s3 import save_to_s3
    if sync_cache:
        s3_file_chksum = save_to_s3(bname='garmin-scripts-cache-ddboline')
    else:
        s3_file_chksum = save_to_s3()

    local_file_chksum = {}

    def process_files(_, dirname, names):
        """ callback function for os.walk """
        for fn_ in names:
            fname = '%s/%s' % (dirname, fn_)
            if not sync_cache:
                if os.path.isdir(fname) or \
                        ('garmin.pkl' in fn_) or \
                        ('garmin.list' in fn_) or \
                        ('.pkl.gz' in fn_) or \
                        ('.avro' in fn_):
                    continue
            cmd = 'md5sum %s' % fname
            md5sum = run_command(cmd, do_popen=True, single_line=True).split()[0]
            md5sum = md5sum.decode()
            if fn_ not in local_file_chksum:
                local_file_chksum[fn_] = md5sum

    walk_dir = '%s/run' % cache_dir
    if sync_cache:
        walk_dir = '%s/run/cache' % cache_dir

    walk_wrapper(walk_dir, process_files, None)

    if not sync_cache:
        local_files_not_in_s3 = [
            '%s/run/gps_tracks/%s' % (cache_dir, fn_)
            if fn_ != 'garmin_corrections.json' else '%s/run/%s' % (cache_dir, fn_)
            for fn_ in local_file_chksum
            if fn_ not in s3_file_chksum or local_file_chksum[fn_] != s3_file_chksum[fn_]
        ]
    else:
        local_files_not_in_s3 = [
            '%s/run/cache/%s' % (cache_dir, fn_) for fn_ in local_file_chksum
            if fn_ not in s3_file_chksum or local_file_chksum[fn_] != s3_file_chksum[fn_]
        ]

    s3_files_not_in_local = [
        fn_ for fn_ in s3_file_chksum
        if fn_ not in local_file_chksum or local_file_chksum[fn_] != s3_file_chksum[fn_]
    ]

    if local_files_not_in_s3:
        print('local_files_not_in_s3')
        print('\n'.join(local_files_not_in_s3))
        if not sync_cache:
            s3_file_chksum = save_to_s3(filelist=local_files_not_in_s3)
        else:
            s3_file_chksum = save_to_s3(
                filelist=local_files_not_in_s3, bname='garmin-scripts-cache-ddboline')
    if s3_files_not_in_local:
        print('missing files', s3_files_not_in_local)


def read_garmin_file(fname, msg_q=None, options=None, s3_files=None):
    """ read single garmin file """
    from garmin_app.garmin_cache import pool
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_parse import GarminParse
    from garmin_app.garmin_report import GarminReport
    from garmin_app.garmin_corrections import list_of_corrected_laps
    if options is None:
        options = {'cache_dir': CACHEDIR, 'do_update': False}
    tcx_job = pool.submit(convert_fit_to_tcx, fname)
    gpx_job = pool.submit(convert_gmn_to_gpx, fname)
    cache_dir = options['cache_dir']

    corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)

    pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
    cache_dir_ = '%s/run/cache' % cache_dir

    avro_file = '%s/%s.avro' % (cache_dir, os.path.basename(fname))
    if not os.path.exists(avro_file):
        s3_cache_files = get_list_of_keys('garmin-scripts-cache-ddboline')
        s3_key = os.path.basename(avro_file)
        if s3_key in s3_cache_files:
            download_from_s3('garmin-scripts-cache-ddboline', s3_key, avro_file)

    cache_ = GarminCache(cache_directory=cache_dir_, corr_list=corr_list_)

    _temp_file = None
    if not options['do_update']:
        _temp_file = cache_.read_cached_gfile(gfbname=os.path.basename(fname))
    if _temp_file:
        _gfile = _temp_file
    else:
        _gfile = GarminParse(fname, corr_list=corr_list_)
        _gfile.read_file()
    if not _gfile:
        return False
    if options['do_update'] or not os.path.exists(avro_file):
        cache_.write_cached_gfile(garminfile=_gfile)
    _report = GarminReport(cache_obj=cache_, msg_q=msg_q, gfile=_gfile)
    print(_report.file_report_txt())
    _report.file_report_html(options=options)
    for fn0, fn1 in ((tcx_job.result(), '/tmp/temp.tcx'), (gpx_job.result(), '/tmp/temp.gpx')):
        if fn0 and os.path.exists(fn0):
            os.rename(fn0, fn1)
    return True


def do_summary(directory_, msg_q=None, options=None):
    """ produce summary report """
    from garmin_app.garmin_cache import (GarminCache, read_pickle_object_in_file,
                                         write_pickle_object_to_file)
    from garmin_app.garmin_corrections import list_of_corrected_laps
    from garmin_app.garmin_corrections_sql import write_corrections_table
    from garmin_app.garmin_report import GarminReport
    if options is None:
        options = {'cache_dir': CACHEDIR}
    cache_dir = options['cache_dir']
    corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)
    pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
    cache_dir_ = '%s/run/cache' % cache_dir
    cache_ = GarminCache(
        cache_directory=cache_dir_,
        corr_list=corr_list_,
        use_sql=True,
        do_tunnel=options.get('do_tunnel', False),
        check_md5=options.get('do_check', False))
    if 'build' in options and options['build']:
        summary_list_ = cache_.get_cache_summary_list(
            directory='%s/run' % cache_dir, options=options)
        cache_ = GarminCache(
            pickle_file=pickle_file_,
            cache_directory=cache_dir_,
            corr_list=corr_list_,
            use_sql=False,
            check_md5=True,
            cache_read_fn=read_pickle_object_in_file,
            cache_write_fn=write_pickle_object_to_file,
            do_tunnel=options.get('do_tunnel', False))
        cache_.cache_write_fn(cache_.cache_summary_file_dict)
        write_corrections_table(corr_list_, do_tunnel=options.get('do_tunnel', False))
        return summary_list_
    summary_list_ = cache_.get_cache_summary_list(directory=directory_, options=options)
    if not summary_list_:
        return False
    _report = GarminReport(cache_obj=cache_, msg_q=msg_q)
    print(_report.summary_report(summary_list_.values(), options=options))
    return True


def add_correction(correction_str, json_path=None, options=None):
    """ add correction to json file """
    from garmin_app.garmin_corrections import (list_of_corrected_laps, save_corrections)
    from garmin_app.garmin_corrections_sql import (read_corrections_table, write_corrections_table)
    l_corr = list_of_corrected_laps(json_path=json_path)
    l_corr.update(read_corrections_table(do_tunnel=options.get('do_tunnel', False)))
    ent = correction_str.split()
    timestr = ent[0]
    try:
        parse(timestr)
    except ValueError:
        return {}
    lapdict = {}
    for idx, line in enumerate(ent[1:]):
        arg = line.split(',')
        tmp_ = []
        if len(arg) == 0:
            continue
        if len(arg) > 0:
            try:
                lapdist = float(arg[0])
            except ValueError:
                continue
            tmp_.append(lapdist)
        if len(arg) > 1:
            try:
                laptime = float(arg[1])
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
        save_corrections(l_corr, json_path='%s/public_html/garmin/files' % HOMEDIR)
    write_corrections_table(l_corr, do_tunnel=options.get('do_tunnel', False))
    return l_corr


def garmin_parse_arg_list(args, options=None, msg_q=None):
    """ parse command line arguments """
    from garmin_app.garmin_cache import GarminCache
    from garmin_app.garmin_cache_sql import write_postgresql_table
    from garmin_app.garmin_corrections import list_of_corrected_laps
    from garmin_app.garmin_corrections_sql import write_corrections_table

    if options is None:
        options = {'cache_dir': CACHEDIR}
    cache_dir = options['cache_dir']

    s3_files = get_list_of_keys()

    gdir = set()
    for arg in args:
        if arg == 'build':
            if msg_q is not None:
                return
            options['build'] = True
        elif arg == 'backup':
            if msg_q is not None:
                return
            fname = '%s/garmin_data_%s.tar.gz'\
                    % (cache_dir, datetime.date.today().strftime('%Y%m%d'))
            run_command('cd %s/run/ ; ' % cache_dir + 'tar zcvf %s gps_tracks/ ' % fname +
                        'garmin_corrections.json')
            if os.path.exists('%s/public_html/backup' % os.getenv('HOME')):
                run_command(
                    'cp %s %s/public_html/backup/garmin_data.tar.gz' % (fname, os.getenv('HOME')))
            if os.path.exists('%s/public_html/garmin/tar' % os.getenv('HOME')):
                run_command('mv %s %s/public_html/garmin/tar' % (fname, os.getenv('HOME')))

            pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
            cache_dir_ = '%s/run/cache' % cache_dir
            corr_list_ = list_of_corrected_laps(json_path='%s/run' % cache_dir)

            write_corrections_table(corr_list_, do_tunnel=options.get('do_tunnel', False))

            cache_ = GarminCache(
                pickle_file=pickle_file_,
                cache_directory=cache_dir_,
                corr_list=corr_list_,
                check_md5=True)
            summary_list_ = cache_.cache_read_fn()
            # backup garmin.pkl.gz info to postgresql database
            write_postgresql_table(summary_list_, do_tunnel=options.get('do_tunnel', False))

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
            add_correction(' '.join(args[1:]), json_path='%s/run' % cache_dir, options=options)
            return
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
                                                                datetime.date.today().year + 1)):
                gdir.update(find_gps_tracks(arg, cache_dir, s3_files=s3_files))
            elif '.gmn' in arg or 'T' in arg:
                files = glob.glob('%s/run/gps_tracks/%s' % (cache_dir, arg))
                gdir.update(files)
            else:
                print('unhandled argument:', arg)
    if not gdir:
        gdir.add('%s/run/gps_tracks' % cache_dir)

    gdir = sorted(gdir)

    if len(gdir) == 1 and os.path.isfile(gdir[0]):
        return read_garmin_file(gdir[0], msg_q=msg_q, options=options, s3_files=s3_files)
    return do_summary(gdir, msg_q=msg_q, options=options)


def find_gps_tracks(arg, cache_dir, s3_files={}):
    """ find gps files matching pattern in cache_dir """
    files = set(glob.glob('%s/run/gps_tracks/%s*' % (cache_dir, arg)))
    files |= set(glob.glob('%s/run/gps_tracks/%s*' % (cache_dir, arg.replace('-', ''))))
    basenames = [f.split('/')[-1] for f in sorted(files)]
    if len([x for x in basenames if x[:10] == basenames[0][:10]]) == \
            len(basenames):
        for fn_ in basenames:
            print(fn_)
    for s3_file in s3_files:
        fname = '%s/run/gps_tracks/%s' % (cache_dir, s3_file)
        if os.path.exists(fname):
            continue
        if arg in s3_file or arg.replace('-', '') in s3_file:
            download_from_s3(s3_file, fname)
            files.add(fname)
    return sorted(files)


def test_find_gps_tracks():
    expect = [
        '2014-07-04_08-27-37-80-5163.fit', '2014-07-04_09-02-20-80-10565.fit',
        '2014-07-04_09-20-35-80-4251.fit'
    ]
    if os.path.exists('%s/run/gps_tracks' % CACHEDIR):
        expect = sorted('%s/run/gps_tracks/%s' % (CACHEDIR, x) for x in expect)
        test = sorted(find_gps_tracks('2014-07-04', CACHEDIR))
        print(test)
        print(expect)
        assert test == expect


def garmin_arg_parse(script_path=BASEDIR, cache_dir=CACHEDIR):
    """ parse command line arguments """
    help_text = 'usage: ./garmin.py <%s>' % '|'.join(COMMANDS)
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('command', nargs='*', help=help_text)
    parser.add_argument('--daemon', '-d', action='store_true', help='run as daemon')
    parser.add_argument('--tunnel', '-t', action='store_true', help='tunnel to postgresql server')
    args = parser.parse_args()

    do_tunnel = False
    if getattr(args, 'tunnel'):
        do_tunnel = True

    for arg in getattr(args, 'command'):
        if any(arg == x for x in ['h', 'help', '-h', '--help']):
            print('usage: ./garmin.py <%s>' % '|'.join(COMMANDS))
            return
        elif arg == 'get':
            raise NotImplementedError()
            if not os.path.exists('%s/run' % cache_dir):
                os.makedirs('%s/run/' % cache_dir)
                os.chdir('%s/run' % cache_dir)

                from garmin_app.garmin_cache import (read_pickle_object_in_file as read_,
                                                     write_pickle_object_to_file as write_)

                pickle_file_ = '%s/run/garmin.pkl.gz' % cache_dir
                summary_list_ = read_(pickle_file=pickle_file_)
                if not summary_list_:
                    from garmin_app.garmin_cache_sql import \
                        write_postgresql_table
                    summary_list_ = write_postgresql_table([],
                                                           get_summary_list=True,
                                                           do_tunnel=do_tunnel)
                    print(len(summary_list_), pickle_file_)
                    # Recreate cache file using list from database
                    write_(summary_list_, pickle_file_)
            return
        if arg == 'sync':
            compare_with_remote(cache_dir)
            compare_with_remote(cache_dir, sync_cache=True)
            return

    if not os.path.exists('%s/run' % cache_dir):
        print('need to download files first')
        return

    options = {
        'do_plot': False,
        'do_year': False,
        'do_month': False,
        'do_week': False,
        'do_day': False,
        'do_file': False,
        'do_sport': None,
        'do_update': False,
        'do_average': False,
        'do_check': False,
        'do_tunnel': False
    }
    options['script_path'] = script_path
    options['cache_dir'] = cache_dir
    options['do_tunnel'] = do_tunnel

    if getattr(args, 'daemon'):
        with garmin_server():
            return None
    return garmin_parse_arg_list(getattr(args, 'command'), options=options)


def report():
    import garmin_app
    from garmin_app import garmin_cache
    """ parse command line arguments """
    help_text = 'usage: ./garmin_report.py <avro file>'
    parser = argparse.ArgumentParser(description='garmin app')
    parser.add_argument('avro_file', nargs=1, help=help_text)
    args = parser.parse_args()

    avro_file = args.avro_file[0]

    gfile = garmin_cache.read_avro_object(avro_file)

    if gfile is None:
        exit(0)

    print(f'{len(gfile.laps)} {len(gfile.points)}')


def main():
    import garmin_app
    return garmin_arg_parse(script_path=garmin_app.__path__[0])
