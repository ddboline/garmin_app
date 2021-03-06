# -*- coding: utf-8 -*-
"""
    functions to generate reports either to STDOUT or html
"""
from __future__ import (print_function, division, print_function, unicode_literals)

import os
import re
import datetime
from collections import defaultdict
try:
    from itertools import izip
except ImportError:
    from builtins import zip as izip

from garmin_app.util import HOMEDIR
from garmin_app.garmin_summary import GarminSummary
from garmin_app.garmin_utils import (print_date_string, print_h_m_s, run_command, days_in_month,
                                     days_in_year, METERS_PER_MILE, MARATHON_DISTANCE_MI,
                                     WEEKDAY_NAMES, MONTH_NAMES, SPORT_TYPES, SPORT_MAP)


def print_history_buttons(history_list):
    """ ... """
    if not history_list:
        return
    retval = []
    for hist in history_list:
        if hist == 'year':
            continue
        retval.append('<button type="submit" onclick="send_command(\'prev ' +
                      '%s\');"> %s </button>' % (hist, hist))
    return '\n'.join(retval)


class GarminReport(object):
    """
        Class to produce reports, to stdout, and to html
        Reports are for:
            individual files
            summaries of files, days, weeks, months and years
    """

    def __init__(self, cache_obj=None, msg_q=None, gfile=None):
        self.cache_obj = cache_obj
        self.msg_q = msg_q
        self.gfile = gfile

    def summary_report(self, summary_list, options, copy_to_public_html=True):
        """ get summary of files in directory """
        opts = ['do_year', 'do_month', 'do_week', 'do_day', 'do_file', 'do_sport', 'do_average']
        do_year, do_month, do_week, do_day, do_file, do_sport, do_average = \
            (options[o] for o in opts)

        if isinstance(summary_list, dict):
            summary_list = sorted(summary_list.values(), key=lambda x: x.begin_datetime)
        else:
            summary_list = sorted(summary_list, key=lambda x: x.begin_datetime)

        year_set = list(set(x.begin_datetime.year for x in summary_list))
        month_set = list(
            set((x.begin_datetime.year * 100 + x.begin_datetime.month) for x in summary_list))
        week_set = list(
            set((x.begin_datetime.isocalendar()[0] * 100 + x.begin_datetime.isocalendar()[1])
                for x in summary_list))
        day_set = list(set(x.begin_datetime.date() for x in summary_list))
        sport_set = list(set(x.sport for x in summary_list))
        for item in year_set, month_set, week_set, day_set, sport_set:
            item.sort()

        total_sport_summary = {s: GarminSummary() for s in sport_set}
        year_sport_summary = {s: {y: GarminSummary() for y in year_set} for s in sport_set}
        month_sport_summary = {s: {m: GarminSummary() for m in month_set} for s in sport_set}
        day_sport_summary = {s: {d: GarminSummary() for d in day_set} for s in sport_set}
        week_sport_summary = {s: {w: GarminSummary() for w in week_set} for s in sport_set}

        total_sport_day_set = {s: set() for s in sport_set}
        year_sport_day_set = {s: {y: set() for y in year_set} for s in sport_set}
        month_sport_day_set = {s: {m: set() for m in month_set} for s in sport_set}
        day_sport_set = {s: set() for s in sport_set}
        week_sport_day_set = {s: {w: set() for w in week_set} for s in sport_set}
        week_sport_set = {s: set() for s in sport_set}

        total_summary = GarminSummary()
        year_summary = {y: GarminSummary() for y in year_set}
        month_summary = {m: GarminSummary() for m in month_set}
        day_summary = {d: GarminSummary() for d in day_set}
        week_summary = {w: GarminSummary() for w in week_set}

        year_day_set = {y: set() for y in year_set}
        month_day_set = {m: set() for m in month_set}
        week_day_set = {w: set() for w in week_set}

        for gfile in summary_list:
            cur_date = gfile.begin_datetime.date()
            month_index = cur_date.year * 100 + cur_date.month
            _ical = cur_date.isocalendar()
            week_index = _ical[0] * 100 + _ical[1]
            sport = gfile.sport
            if do_sport and do_sport not in gfile.sport:
                continue
            year = cur_date.year
            total_sport_summary[sport].add(gfile)
            total_sport_day_set[sport].add(cur_date)
            total_summary.add(gfile)
            year_sport_summary[sport][year].add(gfile)
            year_sport_day_set[sport][year].add(cur_date)
            year_summary[year].add(gfile)
            year_day_set[year].add(cur_date)
            month_sport_summary[sport][month_index].add(gfile)
            month_sport_day_set[sport][month_index].add(cur_date)
            month_summary[month_index].add(gfile)
            month_day_set[month_index].add(cur_date)
            day_sport_summary[sport][cur_date].add(gfile)
            day_sport_set[sport].add(cur_date)
            day_summary[cur_date].add(gfile)
            week_sport_summary[sport][week_index].add(gfile)
            week_sport_day_set[sport][week_index].add(cur_date)
            week_sport_set[sport].add(week_index)
            week_summary[week_index].add(gfile)
            week_day_set[week_index].add(cur_date)

        # If more than one year, default to year-to-year summary
        retval = []
        cmd_args = []
        if do_file:
            for sport in SPORT_TYPES:
                if sport not in sport_set:
                    continue
                for gfile in summary_list:
                    cur_date = gfile.begin_datetime.date()
                    if gfile.sport != sport:
                        continue
                    retval.append(self.day_summary_report_txt(gfile, sport, cur_date))
                    cmd_args.append('%s' % os.path.basename(gfile.filename))
                retval.append('')
            retval.append('')
        if do_day:
            for sport in SPORT_TYPES:
                if sport not in sport_set:
                    continue
                for cur_date in day_set:
                    if cur_date not in day_sport_set[sport]:
                        continue
                    retval.append(
                        self.day_summary_report_txt(day_sport_summary[sport][cur_date], sport,
                                                    cur_date))
                    cmd_args.append('%04d-%02d-%02d file %s' % (cur_date.year, cur_date.month,
                                                                cur_date.day, sport))
                retval.append('')
                if not do_sport and do_average:
                    retval.append(
                        self.day_average_report_txt(total_sport_summary[sport], sport,
                                                    len(day_sport_set[sport])))
                    cmd_args.append('%04d-%02d-%02d file %s' % (cur_date.year, cur_date.month,
                                                                cur_date.day, sport))
                    retval.append('')
            if not do_sport:
                for cur_date in day_set:
                    retval.append(
                        self.day_summary_report_txt(day_summary[cur_date], 'total', cur_date))
                    cmd_args.append('%04d-%02d-%02d file %s' % (cur_date.year, cur_date.month,
                                                                cur_date.day, sport))
                retval.append('')
            if not do_sport and do_average:
                retval.append(self.day_average_report_txt(total_summary, 'total', len(day_set)))
                cmd_args.append('')
                retval.append('')
        if do_week:
            for sport in SPORT_TYPES:
                if sport not in sport_set:
                    continue
                for yearweek in week_set:
                    if len(week_sport_day_set[sport][yearweek]) == 0:
                        continue
                    isoyear = int(yearweek / 100)
                    isoweek = yearweek % 100
                    retval.append(
                        self.week_summary_report_txt(week_sport_summary[sport][yearweek], sport,
                                                     isoyear, isoweek,
                                                     len(week_sport_day_set[sport][yearweek])))
                    cmd_args.append('')
                retval.append('')
                if not do_sport and do_average:
                    retval.append(
                        self.week_average_report_txt(
                            total_sport_summary[sport],
                            sport=sport,
                            number_days=len(total_sport_day_set[sport]),
                            number_of_weeks=len(week_sport_set[sport])))
                    cmd_args.append('')
                    retval.append('')
            for yearweek in week_set:
                isoyear = int(yearweek / 100)
                isoweek = yearweek % 100
                if not do_sport:
                    retval.append(
                        self.week_summary_report_txt(week_summary[yearweek], 'total', isoyear,
                                                     isoweek, len(week_day_set[yearweek])))
                    cmd_args.append('')
            if not do_sport and do_average:
                retval.append('')
                retval.append(
                    self.week_average_report_txt(
                        total_summary,
                        sport='total',
                        number_days=len(day_set),
                        number_of_weeks=len(week_set)))
                cmd_args.append('')
                retval.append('')
        if do_month:
            for sport in SPORT_TYPES:
                if sport not in sport_set:
                    continue
                for yearmonth in month_set:
                    year = int(yearmonth / 100)
                    month = yearmonth % 100
                    if len(month_sport_day_set[sport][yearmonth]) == 0:
                        continue
                    retval.append(
                        self.month_summary_report_txt(month_sport_summary[sport][yearmonth], sport,
                                                      year, month,
                                                      len(month_sport_day_set[sport][yearmonth])))
                    cmd_args.append('%04d-%02d day %s' % (year, month, sport))
                retval.append('')
                if not do_sport and do_average:
                    retval.append(
                        self.month_average_report_txt(
                            total_sport_summary[sport],
                            sport,
                            number_of_months=len(month_sport_day_set[sport])))
                    cmd_args.append('%04d-%02d day %s' % (year, month, sport))
                    retval.append('')
            retval.append('')
            for yearmonth in month_set:
                year = int(yearmonth / 100)
                month = yearmonth % 100
                if len(month_day_set[yearmonth]) == 0:
                    continue
                if not do_sport:
                    retval.append(
                        self.month_summary_report_txt(month_summary[yearmonth], 'total', year,
                                                      month, len(month_day_set[yearmonth])))
                    cmd_args.append('%04d-%02d day' % (year, month))
            retval.append('')
            if not do_sport and do_average:
                retval.append(
                    self.month_average_report_txt(
                        total_summary, sport='total', number_of_months=len(month_set)))
                cmd_args.append('')
                retval.append('')
        if do_year:
            for sport in SPORT_TYPES:
                if sport not in sport_set:
                    continue
                for year in year_set:
                    if len(year_sport_day_set[sport][year]) == 0:
                        continue
                    retval.append(
                        self.year_summary_report_txt(year_sport_summary[sport][year], sport, year,
                                                     len(year_sport_day_set[sport][year])))
                    cmd_args.append('%d month %s' % (year, sport))
                retval.append('')
            retval.append('')
            for year in year_set:
                if len(year_day_set[year]) == 0:
                    continue
                if not do_sport:
                    retval.append(
                        self.year_summary_report_txt(year_summary[year], 'total', year,
                                                     len(year_day_set[year])))
                    cmd_args.append('%d month' % year)
            retval.append('')

        for sport in SPORT_TYPES:
            if sport not in sport_set:
                continue
            if len(total_sport_day_set[sport]) > 1 and not do_day and\
                    do_average:
                retval.append(
                    self.day_average_report_txt(total_sport_summary[sport], sport,
                                                len(day_sport_set[sport])))
        if not do_sport and do_average:
            retval.append('')
            retval.append(self.day_average_report_txt(total_summary, 'total', len(day_set)))
            cmd_args.append('')
            retval.append('')
        for sport in SPORT_TYPES:
            if sport not in sport_set:
                continue
            if len(week_sport_set[sport]) > 1 and not do_week and do_average:
                retval.append(
                    self.week_average_report_txt(
                        total_sport_summary[sport],
                        sport=sport,
                        number_days=len(total_sport_day_set[sport]),
                        number_of_weeks=len(week_sport_set[sport])))
                cmd_args.append('')
        if not do_sport and do_average:
            retval.append('')
            retval.append(
                self.week_average_report_txt(
                    total_summary, 'total', number_days=len(day_set),
                    number_of_weeks=len(week_set)))
            cmd_args.append('')
            retval.append('')
        for sport in SPORT_TYPES:
            if sport not in sport_set:
                continue
            if len(month_sport_day_set[sport]) > 1 and not do_month and\
                    do_average:
                retval.append(
                    self.month_average_report_txt(
                        total_sport_summary[sport],
                        sport,
                        number_of_months=len(month_sport_day_set[sport])))
                cmd_args.append('')
        if not do_sport and do_average:
            retval.append('')
            retval.append(
                self.month_average_report_txt(
                    total_summary, 'total', number_of_months=len(month_set)))
            cmd_args.append('')
            retval.append('')
        begin_date = day_set[0]
        end_date = day_set[-1]
        total_days = (end_date - begin_date).days
        for sport in SPORT_TYPES:
            if sport not in sport_set:
                continue
            if len(total_sport_day_set[sport]) == 0:
                continue
            if not do_sport:
                retval.append(
                    self.total_summary_report_txt(total_sport_summary[sport], sport,
                                                  len(total_sport_day_set[sport]), total_days))
                cmd_args.append('')
        if not do_sport:
            retval.append('')
            retval.append(
                self.total_summary_report_txt(total_summary, 'total', len(day_set), total_days))
            cmd_args.append('')
            retval.append('')

        if 'occur' in options:
            occur_map = defaultdict(int)

            if len(day_set) > 1:
                last_date = day_set[0]
                for day1, day0 in izip(day_set[1:], day_set):
                    if (day1 - day0).days > 1:
                        occur_map[(day0 - last_date).days + 1] += 1
                        if ((day0 - last_date).days + 1) > 5:
                            retval.append(day0)
                            cmd_args.append('')
                        last_date = day1
                try:
                    occur_map[(day_set[-1] - last_date).days + 1] += 1
                except KeyError:
                    print(day_set[-1], last_date)
                    print((day_set[-1] - last_date).days + 1)
                    print(occur_map)
                    print(day_set)
                    print('key error')
                    raise KeyError

                if not do_sport:
                    for i in sorted(occur_map):
                        retval.append('%s %s' % (i, occur_map[i]))
        outstr = re.sub('\n\n+', '\n', '\n'.join(retval))

        htmlostr = []
        for ent in retval:
            htmlostr.append(ent)
            if not ent:
                continue
            if cmd_args:
                cmd = cmd_args.pop(0)
                if cmd:
                    for o, n in SPORT_MAP.items():
                        if o != n:
                            cmd = cmd.replace(o, n)
                    htmlostr[-1] = '<button type="submit" ' +\
                                   'onclick="send_command(\'%s\');">' % cmd +\
                                   '%s</button> %s' % (cmd, ent.strip())
        htmlostr = re.sub('\n\n+', '<br>\n', '\n'.join(htmlostr))
        cache_dir = options['cache_dir']
        script_path = options['script_path']
        if not os.path.exists('%s/html' % cache_dir):
            os.makedirs('%s/html' % cache_dir)
        with open('%s/html/index.html' % cache_dir, 'wt') as htmlfile:
            with open('%s/templates/GARMIN_TEMPLATE.html' % script_path, 'rt') as infile:
                for line in infile:
                    if 'INSERTTEXTHERE' in line:
                        htmlfile.write(htmlostr)
                    elif 'SPORTTITLEDATE' in line:
                        newtitle = 'Garmin Summary'
                        htmlfile.write(line.replace('SPORTTITLEDATE', newtitle))
                    elif 'HISTORYBUTTONS' in line:
                        if self.msg_q:
                            htmlfile.write(
                                line.replace('HISTORYBUTTONS', print_history_buttons(self.msg_q)))
                    else:
                        htmlfile.write(line)

        if os.path.exists('%s/html' % cache_dir) and copy_to_public_html:
            if not os.path.exists('%s/public_html/garmin' % HOMEDIR):
                os.makedirs('%s/public_html/garmin' % HOMEDIR)
            if os.path.exists('%s/public_html/garmin/html' % HOMEDIR):
                run_command('rm -rf %s/public_html/garmin/html' % HOMEDIR)
            run_command('mv %s/html %s/public_html/garmin' % (cache_dir, HOMEDIR))
        return outstr

    def file_report_txt(self):
        """ nice output string for a file """
        assert self.gfile is not None
        gfile = self.gfile
        retval = ['Start time %s' % print_date_string(gfile.begin_datetime)]

        for lap in gfile.laps:
            retval.append(print_lap_string(lap, gfile.sport))

        min_mile = 0
        mi_per_hr = 0
        if gfile.total_distance > 0:
            min_mile = (gfile.total_duration / 60.) / (gfile.total_distance / METERS_PER_MILE)
        if gfile.total_duration > 0:
            mi_per_hr = ((gfile.total_distance / METERS_PER_MILE) /
                         (gfile.total_duration / 60. / 60.))

        tmpstr = []
        if gfile.sport == 'running':
            tmpstr.append('total %.2f mi %s calories %s time %s min/mi %s min/km' %
                          (gfile.total_distance / METERS_PER_MILE, gfile.total_calories,
                           print_h_m_s(gfile.total_duration), print_h_m_s(min_mile * 60, False),
                           print_h_m_s(min_mile * 60 / METERS_PER_MILE * 1000., False)))
        else:
            tmpstr.append('total %.2f mi %s calories %s time %.2f mph' %
                          (gfile.total_distance / METERS_PER_MILE, gfile.total_calories,
                           print_h_m_s(gfile.total_duration), mi_per_hr))
        if gfile.total_hr_dur > 0:
            tmpstr.append('%i bpm' % (gfile.total_hr_dur / gfile.total_hr_dis))
        retval.append(' '.join(tmpstr))
        retval.append('')
        retval.append(print_splits(gfile, METERS_PER_MILE))
        retval.append('')
        retval.append(print_splits(gfile, 5000., 'km'))

        avg_hr = 0
        sum_time = 0
        hr_vals = []
        for point in gfile.points:
            if point.heart_rate and point.heart_rate > 0:
                avg_hr += point.heart_rate * point.duration_from_last
                sum_time += point.duration_from_last
                hr_vals.append(point.heart_rate)
        if sum_time > 0:
            avg_hr /= sum_time
            if len(hr_vals) > 0:
                retval.append('Heart Rate %2.2f avg %2.2f max' % (avg_hr, max(hr_vals)))

        alt_vals = []
        vertical_climb = 0
        for point in gfile.points:
            if point.altitude and point.altitude > 0 and point.altitude < 10000:
                alt_vals.append(point.altitude)
                if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2]:
                    vertical_climb += alt_vals[-1] - alt_vals[-2]
        if len(alt_vals) > 0:
            retval.append('max altitude diff: %.2f m' % (max(alt_vals) - min(alt_vals)))
            retval.append('vertical climb: %.2f m' % vertical_climb)
        retval.append('')

        return '\n'.join(retval)

    def file_report_html(self, options=None, use_time=False, copy_to_public_html=True):
        """ create pretty plots """
        assert self.gfile is not None
        gfile = self.gfile
        avg_hr, sum_time, max_hr = 0, 0, 0
        hr_vals, hr_values, alt_vals, alt_values = [], [], [], []
        if not options:
            options = {'cache_dir': None, 'script_path': None}
        speed_values = get_splits(gfile, 400., do_heart_rate=True)
        heart_rate_speed = [(h, 4 * t / 60.) for d, t, h in speed_values]
        if speed_values:
            speed_values = [(d / 4., 4 * t / 60.) for d, t, h in speed_values]
        mph_speed_values = []
        avg_speed_values = []
        avg_mph_speed_values = []
        lat_vals = []
        lon_vals = []
        graphs = []
        mile_split_vals = get_splits(gfile, METERS_PER_MILE, do_heart_rate=False)
        if mile_split_vals:
            mile_split_vals = [(d, t / 60.) for d, t in mile_split_vals]
        for point in gfile.points:
            if point.distance is None:
                continue
            if use_time:
                xval = point.duration_from_begin
            else:
                xval = point.distance / METERS_PER_MILE
            if xval and xval > 0 and point.heart_rate and point.heart_rate > 0:
                avg_hr += point.heart_rate * point.duration_from_last
                sum_time += point.duration_from_last
                hr_vals.append(point.heart_rate)
                hr_values.append([xval, point.heart_rate])
            if point.altitude > 0 and point.altitude < 10000:
                alt_vals.append(point.altitude)
                alt_values.append([xval, point.altitude])
            if point.speed_mph > 0 and point.speed_mph < 20:
                mph_speed_values.append([xval, point.speed_mph])
            if point.avg_speed_value_permi > 0\
                    and point.avg_speed_value_permi < 20:
                avg_speed_values.append([xval, point.avg_speed_value_permi])
            if point.avg_speed_value_mph > 0:
                avg_mph_speed_values.append([xval, point.avg_speed_value_mph])
            if point.latitude and point.longitude:
                lat_vals.append(point.latitude)
                lon_vals.append(point.longitude)
        if sum_time > 0:
            avg_hr /= sum_time
            max_hr = max(hr_vals)

        cache_dir = options['cache_dir']
        script_path = options['script_path']
        if not os.path.exists('%s/html' % cache_dir):
            os.makedirs('%s/html' % cache_dir)

        if len(mile_split_vals) > 0:
            options = {
                'plotopt': {
                    'marker': 'o'
                },
                'xlabel': 'mi',
                'ylabel': 'min/mi',
                'cache_dir': cache_dir
            }
            graphs.append(
                plot_graph(
                    name='mile_splits',
                    title='Pace per Mile every mi',
                    data=mile_split_vals,
                    opts=options))

        if len(hr_values) > 0:
            options = {'xlabel': 'mi', 'ylabel': 'bpm', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='heart_rate',
                    title='Heart Rate %2.2f avg %2.2f max' % (avg_hr, max_hr),
                    data=hr_values,
                    opts=options))
        if len(alt_values) > 0:
            options = {'xlabel': 'mi', 'ylabel': 'height [m]', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(name='altitude', title='Altitude', data=alt_values, opts=options))
        if len(speed_values) > 0:
            options = {'xlabel': 'mi', 'ylabel': 'min/mi', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='speed_minpermi',
                    title='Speed min/mi every 1/4 mi',
                    data=speed_values,
                    opts=options))
            options = {'xlabel': 'mi', 'ylabel': 'mph', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='speed_mph', title='Speed mph', data=mph_speed_values, opts=options))
        if len(heart_rate_speed) > 0:
            options = {'xlabel': 'hrt', 'ylabel': 'min/mi', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='heartrate_vs_speed',
                    title='Speed min/mi every 1/4 mi',
                    data=heart_rate_speed,
                    do_scatter=True,
                    opts=options))
        if len(avg_speed_values) > 0:
            avg_speed_value_min = int(avg_speed_values[-1][1])
            avg_speed_value_sec = int((avg_speed_values[-1][1] - avg_speed_value_min) * 60.)
            options = {'xlabel': 'mi', 'ylabel': 'mph', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='avg_speed_minpermi',
                    title='Avg Speed %i:%02i min/mi' % (avg_speed_value_min, avg_speed_value_sec),
                    data=avg_speed_values,
                    opts=options))

        if len(avg_mph_speed_values) > 0:
            avg_mph_speed_value = avg_mph_speed_values[-1][1]
            options = {'xlabel': 'mi', 'ylabel': 'min/mi', 'cache_dir': cache_dir}
            graphs.append(
                plot_graph(
                    name='avg_speed_mph',
                    title='Avg Speed %.2f mph' % avg_mph_speed_value,
                    data=avg_mph_speed_values,
                    opts=options))

        with open('%s/html/index.html' % cache_dir, 'wt') as htmlfile:
            if len(lat_vals) > 0 and len(lon_vals) > 0 \
                    and len(lat_vals) == len(lon_vals):
                minlat, maxlat = min(lat_vals), max(lat_vals)
                minlon, maxlon = min(lon_vals), max(lon_vals)
                central_lat = (maxlat + minlat) / 2.
                central_lon = (maxlon + minlon) / 2.
                latlon_min = max((maxlat - minlat), (maxlon - minlon))
                latlon_thresholds = [[15, 0.015], [14, 0.038], [13, 0.07], [12, 0.12], [11, 0.20],
                                     [10, 0.4]]
                with open('%s/templates/MAP_TEMPLATE.html' % script_path, 'rt') as infile:
                    for line in infile:
                        if 'SPORTTITLEDATE' in line:
                            newtitle = 'Garmin Event %s on %s' \
                                       % (gfile.sport.title(),
                                          gfile.begin_datetime)
                            htmlfile.write(line.replace('SPORTTITLEDATE', newtitle))
                        elif 'ZOOMVALUE' in line:
                            for zoom, thresh in latlon_thresholds:
                                if latlon_min < thresh or zoom == 10:
                                    htmlfile.write(line.replace('ZOOMVALUE', '%d' % zoom))
                                    break
                        elif 'INSERTTABLESHERE' in line:
                            htmlfile.write('%s\n' % get_file_html(gfile))
                            _tmp = get_html_splits(
                                gfile, split_distance_in_meters=METERS_PER_MILE, label='mi')
                            if _tmp is not None:
                                htmlfile.write('<br><br>%s\n' % _tmp)
                            _tmp = get_html_splits(
                                gfile, split_distance_in_meters=5000., label='km')
                            if _tmp is not None:
                                htmlfile.write('<br><br>%s\n' % _tmp)
                        elif 'INSERTMAPSEGMENTSHERE' in line:
                            for latv, lonv in izip(lat_vals, lon_vals):
                                htmlfile.write('new google.maps.LatLng(%f,%f),\n' % (latv, lonv))
                        elif 'MINLAT' in line or 'MAXLAT' in line\
                                or 'MINLON' in line or 'MAXLON' in line:
                            htmlfile.write(
                                line.replace('MINLAT', '%s' % minlat).replace(
                                    'MAXLAT', '%s' % maxlat).replace('MINLON', '%s' % minlon)
                                .replace('MAXLON', '%s' % maxlon))
                        elif 'CENTRALLAT' in line or 'CENTRALLON' in line:
                            htmlfile.write(
                                line.replace('CENTRALLAT', '%s' % central_lat).replace(
                                    'CENTRALLON', '%s' % central_lon))
                        elif 'INSERTOTHERIMAGESHERE' in line:
                            for gfile in graphs:
                                htmlfile.write('<p>\n<img src="%s">\n</p>' % gfile)
                        elif 'HISTORYBUTTONS' in line:
                            if self.msg_q:
                                htmlfile.write(
                                    line.replace('HISTORYBUTTONS', print_history_buttons(
                                        self.msg_q)))
                        else:
                            htmlfile.write(line)
            else:
                with open('%s/templates/GARMIN_TEMPLATE.html' % script_path, 'rt') as infile:
                    for line in infile:
                        if 'INSERTTEXTHERE' in line:
                            htmlfile.write('%s\n' % get_file_html(gfile))
                            _tmp = get_html_splits(
                                gfile, split_distance_in_meters=METERS_PER_MILE, label='mi')
                            if _tmp is not None:
                                htmlfile.write('<br><br>%s\n' % _tmp)
                            _tmp = get_html_splits(
                                gfile, split_distance_in_meters=5000., label='km')
                            if _tmp is not None:
                                htmlfile.write('<br><br>%s\n' % _tmp)
                        elif 'SPORTTITLEDATE' in line:
                            newtitle = 'Garmin Event %s on %s' \
                                % (gfile.sport.title(), gfile.begin_datetime)
                            htmlfile.write(line.replace('SPORTTITLEDATE', newtitle))
                        elif 'HISTORYBUTTONS' in line:
                            if self.msg_q:
                                htmlfile.write(
                                    line.replace('HISTORYBUTTONS', print_history_buttons(
                                        self.msg_q)))
                        else:
                            htmlfile.write(
                                line.replace('<pre>', '<div>').replace('</pre>', '</div>'))

        if copy_to_public_html and (os.path.exists('%s/html' % cache_dir) and
                                    os.path.exists('%s/public_html/garmin' % HOMEDIR)):
            if os.path.exists('%s/public_html/garmin/html' % HOMEDIR):
                run_command('rm -rf %s/public_html/garmin/html' % HOMEDIR)
            run_command('mv %s/html %s/public_html/garmin' % (cache_dir, HOMEDIR))
            return '%s/public_html/garmin/html' % HOMEDIR
        return '%s/html' % cache_dir

    @staticmethod
    def total_summary_report_txt(gsum, sport=None, number_days=0, total_days=0):
        """ print summary of total information """
        retval = [
            '%17s %10s \t %10s \t %10s \t' %
            (' ', sport, '%4.2f mi' % (gsum.total_distance / METERS_PER_MILE),
             '%i cal' % gsum.total_calories)
        ]

        if sport == 'running' or sport == 'walking':
            retval.append(' %10s \t' %
                          ('%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False)))
            retval.append(' %10s \t' %
                          ('%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False)))
        elif sport == 'biking':
            retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                      (gsum.total_duration / 60. / 60.))))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration)))
        if gsum.total_hr_dur > 0 and sport != 'total':
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        if number_days > 0 and total_days > 0:
            retval.append('%16s' % ('%i / %i days' % (number_days, total_days)))
        return ' '.join(retval)

    @staticmethod
    def day_summary_report_txt(gsum, sport=None, cur_date=None):
        """ print day summary information """
        if not cur_date:
            cur_date = datetime.date.today()
        retval = []
        week = cur_date.isocalendar()[1]
        weekdayname = WEEKDAY_NAMES[cur_date.weekday()]
        if sport == 'running' or sport == 'walking':
            if gsum.total_distance > 0:
                retval.append(
                    '%17s %10s \t %10s \t %10s \t %10s \t %10s \t %10s' %
                    ('%10s %02i %3s' % (cur_date, week, weekdayname), sport, '%.2f mi' %
                     (gsum.total_distance / METERS_PER_MILE), '%i cal' % gsum.total_calories,
                     '%s / mi' % print_h_m_s(gsum.total_duration /
                                             (gsum.total_distance / METERS_PER_MILE), False),
                     '%s / km' % print_h_m_s(gsum.total_duration /
                                             (gsum.total_distance / 1000.), False),
                     print_h_m_s(gsum.total_duration)))
            else:
                retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s \t %10s' %
                              ('%10s %02i %3s' % (cur_date, week, weekdayname), sport,
                               '%.2f mi' % (gsum.total_distance / METERS_PER_MILE),
                               '%i cal' % gsum.total_calories, '         / mi', '         / km',
                               print_h_m_s(gsum.total_duration)))
        elif sport == 'biking':
            retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s' %
                          ('%10s %02i %3s' % (cur_date, week, weekdayname), sport, '%.2f mi' %
                           (gsum.total_distance / METERS_PER_MILE), '%i cal' % gsum.total_calories,
                           '%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                         (gsum.total_duration / 60. / 60.)),
                           print_h_m_s(gsum.total_duration)))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s' %
                          ('%10s %02i %3s' % (cur_date, week, weekdayname), sport,
                           '%.2f mi' % (gsum.total_distance / METERS_PER_MILE),
                           '%i cal' % gsum.total_calories, ' ', print_h_m_s(gsum.total_duration)))
        if gsum.total_hr_dur > 0:
            retval.append('\t %7s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis)))
        return ' '.join(retval)

    @staticmethod
    def day_average_report_txt(gsum, sport=None, number_days=0):
        """ print day average information """
        retval = []
        if number_days == 0:
            return ''
        if sport == 'running' or sport == 'walking':
            retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s \t %10s' %
                          ('average / day', sport,
                           '%.2f mi' % (gsum.total_distance / METERS_PER_MILE / number_days),
                           '%i cal' % (gsum.total_calories / number_days),
                           '%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False),
                           '%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False),
                           print_h_m_s(gsum.total_duration / number_days)))
        elif sport == 'biking':
            retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s' %
                          ('average / day', sport,
                           '%.2f mi' % (gsum.total_distance / METERS_PER_MILE / number_days),
                           '%i cal' % (gsum.total_calories / number_days),
                           '%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                         (gsum.total_duration / 60. / 60.)),
                           print_h_m_s(gsum.total_duration / number_days)))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t %10s \t %10s' %
                          ('average / day', sport,
                           '%.2f mi' % (gsum.total_distance / METERS_PER_MILE / number_days),
                           '%i cal' % (gsum.total_calories / number_days), ' ',
                           print_h_m_s(gsum.total_duration / number_days)))
        if gsum.total_hr_dur > 0:
            retval.append('\t %7s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis)))
        return ' '.join(retval)

    @staticmethod
    def week_summary_report_txt(gsum,
                                sport=None,
                                isoyear=None,
                                isoweek=None,
                                number_in_week=0,
                                date=None):
        """ print week summary information """
        if not date:
            date = datetime.datetime.today()
        if not isoyear:
            isoyear = date.isocalendar()[0]
        if not isoweek:
            isoweek = date.isocalendar()[1]
        if not number_in_week:
            number_in_week = gsum.number_of_items

        total_days = 7
        if datetime.datetime.today().isocalendar()[0] == isoyear\
                and datetime.datetime.today().isocalendar()[1] == isoweek:
            total_days = datetime.datetime.today().isocalendar()[2]

        retval = []
        if sport == 'total':
            retval.append('%17s %10s \t %10s \t %10s \t' % ('%i week %02i' % (isoyear,
                                                                              isoweek), sport, ' ',
                                                            '%i cal' % gsum.total_calories))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('%i week %02i' % (isoyear, isoweek), sport, '%4.2f mi' %
                           (gsum.total_distance / METERS_PER_MILE), '%i cal' % gsum.total_calories))

        if sport == 'running' or sport == 'walking':
            if gsum.total_distance > 0:
                retval.append(
                    ' %10s \t' %
                    ('%s / mi' % print_h_m_s(gsum.total_duration /
                                             (gsum.total_distance / METERS_PER_MILE), False)))
                retval.append(' %10s \t' %
                              ('%s / km' % print_h_m_s(gsum.total_duration /
                                                       (gsum.total_distance / 1000.), False)))
            else:
                retval.append(' %10s \t' % (''))
                retval.append(' %10s \t' % (''))
        elif sport == 'biking':
            retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                      (gsum.total_duration / 60. / 60.))))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration)))
        if gsum.total_hr_dur > 0 and sport != 'total':
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        retval.append('%16s' % ('%i / %i days' % (number_in_week, total_days)))
        return ' '.join(retval)

    @staticmethod
    def week_average_report_txt(gsum, sport=None, number_days=0, number_of_weeks=0):
        """ print week average information """
        if number_of_weeks == 0:
            return
        retval = []
        if sport == 'total':
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('avg / %3s weeks' % number_of_weeks, sport, ' ',
                           '%i cal' % (gsum.total_calories / number_of_weeks)))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('avg / %3s weeks' % number_of_weeks, sport,
                           '%4.2f mi' % (gsum.total_distance / METERS_PER_MILE / number_of_weeks),
                           '%i cal' % (gsum.total_calories / number_of_weeks)))

        if sport == 'running' or sport == 'walking':
            retval.append(' %10s \t' %
                          ('%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False)))
            retval.append(' %10s \t' %
                          ('%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False)))
        elif sport == 'biking':
            retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                      (gsum.total_duration / 60. / 60.))))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration / number_of_weeks)))
        if gsum.total_hr_dur > 0 and sport != 'total':
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        retval.append('%16s' % ('%.1f / %i days' % (float(number_days) / number_of_weeks, 7)))
        return ' '.join(retval)

    @staticmethod
    def month_summary_report_txt(gsum, sport=None, year=None, month=None, number_in_month=0):
        """ print month summary information """
        if not year:
            year = datetime.date.today().year
        if not month:
            month = datetime.date.today().month
        total_days = days_in_month(month=month, year=year)
        if datetime.datetime.today().year == year\
                and datetime.datetime.today().month == month:
            total_days = (datetime.datetime.today() - datetime.datetime(
                datetime.datetime.today().year, datetime.datetime.today().month, 1)).days
        retval = []
        if sport == 'total':
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('%i %s' % (year, MONTH_NAMES[month - 1]), sport, ' ',
                           '%i cal' % gsum.total_calories))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('%i %s' % (year, MONTH_NAMES[month - 1]), sport, '%4.2f mi' %
                           (gsum.total_distance / METERS_PER_MILE), '%i cal' % gsum.total_calories))
        if sport == 'running' or sport == 'walking':
            retval.append(' %10s \t' %
                          ('%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False)))
            retval.append(' %10s \t' %
                          ('%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False)))
        elif sport == 'biking':
            retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                      (gsum.total_duration / 60. / 60.))))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration)))
        if gsum.total_hr_dur > 0:
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        retval.append('%16s' % ('%i / %i days' % (number_in_month, total_days)))
        return ' '.join(retval)

    @staticmethod
    def month_average_report_txt(gsum, sport=None, number_of_months=0):
        """ print month average information """
        if number_of_months == 0:
            return ''
        retval = []
        if sport == 'total':
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('average / month', sport, ' ',
                           '%i cal' % (gsum.total_calories / number_of_months)))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          ('average / month', sport,
                           '%4.2f mi' % (gsum.total_distance / METERS_PER_MILE / number_of_months),
                           '%i cal' % (gsum.total_calories / number_of_months)))
        if sport == 'running' or sport == 'walking':
            retval.append(' %10s \t' %
                          ('%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False)))
            retval.append(' %10s \t' %
                          ('%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False)))
        elif sport == 'biking':
            if gsum.total_duration > 0:
                retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                          (gsum.total_duration / 60. / 60.))))
            else:
                retval.append(' %10s \t' % ('0.0 mph'))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration / number_of_months)))
        if gsum.total_hr_dur > 0:
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        return ' '.join(retval)

    @staticmethod
    def year_summary_report_txt(gsum, sport=None, year=None, number_in_year=0):
        """ print year summary information """
        if not year:
            year = datetime.date.today().year
        retval = []
        total_days = days_in_year(year)
        if datetime.datetime.today().year == year:
            total_days = (datetime.datetime.today() -
                          datetime.datetime(datetime.datetime.today().year, 1, 1)).days
        if sport == 'total':
            retval.append('%17s %10s \t %10s \t %10s \t' % (year, sport, ' ',
                                                            '%i cal' % gsum.total_calories))
        else:
            retval.append('%17s %10s \t %10s \t %10s \t' %
                          (year, sport, '%4.2f mi' % (gsum.total_distance / METERS_PER_MILE),
                           '%i cal' % gsum.total_calories))
        if sport == 'running' or sport == 'walking':
            retval.append(' %10s \t' %
                          ('%s / mi' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / METERS_PER_MILE), False)))
            retval.append(' %10s \t' %
                          ('%s / km' % print_h_m_s(gsum.total_duration /
                                                   (gsum.total_distance / 1000.), False)))
        elif sport == 'biking':
            retval.append(' %10s \t' % ('%.2f mph' % ((gsum.total_distance / METERS_PER_MILE) /
                                                      (gsum.total_duration / 60. / 60.))))
        else:
            retval.append(' %10s \t' % ' ')
        retval.append(' %10s \t' % (print_h_m_s(gsum.total_duration)))
        if gsum.total_hr_dur > 0:
            retval.append(' %7s %2s' % ('%i bpm' % (gsum.total_hr_dur / gsum.total_hr_dis), ' '))
        else:
            retval.append(' %7s %2s' % (' ', ' '))
        retval.append('%16s' % ('%i / %i days' % (number_in_year, total_days)))
        return ' '.join(retval)


def print_lap_string(glap, sport):
    """ print nice output for a lap """
    if glap.lap_number is None:
        return ''
    outstr = [
        '%s lap %i %.2f mi %s %s calories %.2f min' %
        (sport, glap.lap_number, glap.lap_distance / METERS_PER_MILE,
         print_h_m_s(glap.lap_duration), glap.lap_calories, glap.lap_duration / 60.)
    ]
    if sport == 'running':
        if glap.lap_distance > 0:
            outstr.extend([
                print_h_m_s(glap.lap_duration / (glap.lap_distance / METERS_PER_MILE), False),
                '/ mi ',
                print_h_m_s(glap.lap_duration / (glap.lap_distance / 1000.), False), '/ km'
            ])
    if glap.lap_avg_hr and glap.lap_avg_hr > 0:
        outstr.append('%i bpm' % glap.lap_avg_hr)

    return ' '.join(outstr)


def get_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi', do_heart_rate=True):
    """ get splits for given split distance """
    if len(gfile.points) < 3:
        return []
    last_point_me = 0
    last_point_time = 0
    prev_split_time = 0
    avg_hrt_rate = 0
    split_vector = []

    for point in gfile.points:
        cur_point_me = point.distance
        cur_point_time = point.duration_from_begin
        if cur_point_me is None or last_point_me is None:
            continue
        if (cur_point_me - last_point_me) <= 0:
            continue
        if point.heart_rate:
            try:
                avg_hrt_rate += point.heart_rate * (cur_point_time - last_point_time)
            except ValueError as exc:
                print('Exception:', exc, point.heart_rate, cur_point_time, last_point_me)
                raise exc
        nmiles = int(cur_point_me/split_distance_in_meters) \
            - int(last_point_me/split_distance_in_meters)
        if nmiles > 0:
            cur_split_me = int(cur_point_me/split_distance_in_meters) \
                * split_distance_in_meters
            cur_split_time = (last_point_time + (cur_point_time - last_point_time) /
                              (cur_point_me - last_point_me) * (cur_split_me - last_point_me))
            time_val = (cur_split_time - prev_split_time)
            split_dist = cur_point_me / split_distance_in_meters
            if label == 'km':
                split_dist = cur_point_me / 1000.

            tmp_vector = [split_dist, time_val]
            if do_heart_rate:
                tmp_vector.append(avg_hrt_rate / (cur_split_time - prev_split_time))
            split_vector.append(tmp_vector)

            prev_split_time = cur_split_time
            avg_hrt_rate = 0
        last_point_me = cur_point_me
        last_point_time = cur_point_time

    return split_vector


def print_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi'):
    """ print split time for given split distance """
    if len(gfile.points) == 0:
        return ''

    retval = []
    split_vector = get_splits(gfile, split_distance_in_meters, label)
    if not split_vector:
        return ''
    for dis, tim, hrt in split_vector:
        retval.append(
            '%i %s \t %s \t %s / mi \t %s / km \t %s \t %i bpm avg' %
            (dis, label, print_h_m_s(tim),
             print_h_m_s(tim / (split_distance_in_meters / METERS_PER_MILE), False),
             print_h_m_s(tim / (split_distance_in_meters / 1000.), False),
             print_h_m_s(tim /
                         (split_distance_in_meters / METERS_PER_MILE) * MARATHON_DISTANCE_MI), hrt))
    return '\n'.join(retval)


def plot_graph(name=None, title=None, data=None, do_scatter=False, opts={}):
    """ graphics plotting function """
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl

    cache_dir = opts['cache_dir']
    popts = {}
    if 'plotopt' in opts:
        popts = opts['plotopt']
    pl.clf()
    xar, yar = zip(*data)
    xar, yar = [np.array(x) for x in (xar, yar)]
    if do_scatter:
        pl.hist2d(xar, yar, bins=10, **popts)
        #pl.hexbin(xar, yar, gridsize=30, **popts)
    else:
        pl.plot(xar, yar, **popts)
        xmin, xmax, ymin, ymax = pl.axis()
        xmin, ymin = [z - 0.1 * abs(z) for z in (xmin, ymin)]
        xmax, ymax = [z + 0.1 * abs(z) for z in (xmax, ymax)]
        pl.axis([xmin, xmax, ymin, ymax])
    if 'xlabel' in opts:
        pl.xlabel(opts['xlabel'], horizontalalignment='right')
    if 'ylabel' in opts:
        pl.ylabel(opts['ylabel'], verticalalignment='top')
    pl.title(title)
    pl.savefig('%s/html/%s.png' % (cache_dir, name))
    return '%s.png' % name


def get_file_html(gfile):
    """ nice output html for a file """
    retval = []
    retval.append('<table border="1" class="dataframe">')
    retval.append('<thead><tr style="text-align: center;"><th>Start Time</th>'
                  '<th>Sport</th></tr></thead>')
    retval.append('<tbody><tr style="text-align: center;"><td>%s</td><td>%s</td>' %
                  (print_date_string(gfile.begin_datetime), gfile.sport) + '</tr></tbody>')
    retval.append('</table><br>')

    labels = [
        'Sport', 'Lap', 'Distance', 'Duration', 'Calories', 'Time', 'Pace / mi', 'Pace / km',
        'Heart Rate'
    ]
    retval.append('<table border="1" class="dataframe">')
    retval.append('<thead><tr style="text-align: center;">')
    for label in labels:
        retval.append('<th>%s</th>' % label)
    retval.append('</tr></thead>')
    retval.append('<tbody>')
    for lap in gfile.laps:
        retval.append('<tr style="text-align: center;">')
        retval.extend(get_lap_html(lap, gfile.sport))
        retval.append('</tr>')
    retval.append('</tbody></table><br>')

    min_mile = 0
    mi_per_hr = 0
    if gfile.total_distance > 0:
        min_mile = (gfile.total_duration / 60.) / (gfile.total_distance / METERS_PER_MILE)
    if gfile.total_duration > 0:
        mi_per_hr = ((gfile.total_distance / METERS_PER_MILE) / (gfile.total_duration / 60. / 60.))
    if gfile.sport == 'running':
        labels = ['', 'Distance', 'Calories', 'Time', 'Pace / mi', 'Pace / km']
        values = [
            'total',
            '%.2f mi' % (gfile.total_distance / METERS_PER_MILE), gfile.total_calories,
            print_h_m_s(gfile.total_duration),
            print_h_m_s(min_mile * 60, False),
            print_h_m_s(min_mile * 60 / METERS_PER_MILE * 1000., False)
        ]
    else:
        labels = ['total', 'Distance', 'Calories', 'Time', 'Pace mph']
        values = [
            '',
            '%.2f mi' % (gfile.total_distance / METERS_PER_MILE), gfile.total_calories,
            print_h_m_s(gfile.total_duration), mi_per_hr
        ]
    if gfile.total_hr_dur > 0:
        labels.append('Heart Rate')
        values.append('%i bpm' % (gfile.total_hr_dur / gfile.total_hr_dis))

    retval.append('<table border="1" class="dataframe">')
    retval.append('<thead><tr style="text-align: center;">')
    for label in labels:
        retval.append('<th>%s</th>' % label)
    retval.append('</tr></thead>')
    retval.append('<tbody><tr style="text-align: center;">')
    for value in values:
        retval.append('<td>%s</td>' % value)
    retval.append('</tr></tbody></table>')

    return '\n'.join(retval)


def get_lap_html(glap, sport):
    """ return formatted lap html """
    values = [
        sport, glap.lap_number,
        '%.2f mi' % (glap.lap_distance / METERS_PER_MILE),
        print_h_m_s(glap.lap_duration), glap.lap_calories,
        '%.2f min' % (glap.lap_duration / 60.)
    ]
    if glap.lap_distance > 0:
        values.extend([
            '%s / mi' % print_h_m_s(glap.lap_duration /
                                    (glap.lap_distance / METERS_PER_MILE), False),
            '%s / km' % print_h_m_s(glap.lap_duration / (glap.lap_distance / 1000.), False)
        ])
    if glap.lap_avg_hr:
        values.append('%i bpm' % glap.lap_avg_hr)

    return ['<td>%s</td>' % v for v in values]


def get_html_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi'):
    """ print split time for given split distance """
    if len(gfile.points) == 0:
        return None

    labels = ['Split', 'Time', 'Pace / mi', 'Pace / km', 'Marathon Time', 'Heart Rate']
    values = []

    split_vector = get_splits(gfile, split_distance_in_meters, label)
    for dis, tim, hrt in split_vector:
        tmp_vector = [
            '%i %s' % (dis, label),
            print_h_m_s(tim),
            print_h_m_s(tim / (split_distance_in_meters / METERS_PER_MILE), False),
            print_h_m_s(tim / (split_distance_in_meters / 1000.), False),
            print_h_m_s(tim / (split_distance_in_meters / METERS_PER_MILE) * MARATHON_DISTANCE_MI),
            '%i bpm' % hrt
        ]
        values.append(tmp_vector)

    retval = []
    retval.append('<table border="1" class="dataframe">')
    retval.append('<thead><tr style="text-align: center;">')
    for label in labels:
        retval.append('<th>%s</th>' % label)
    retval.append('</tr></thead>')
    retval.append('<tbody>')
    for line in values:
        retval.append('<tr style="text-align: center;">')
        for val in line:
            retval.append('<td>%s</td>' % val)
        retval.append('</tr>')
    retval.append('</tbody></table>')

    return '\n'.join(retval)
