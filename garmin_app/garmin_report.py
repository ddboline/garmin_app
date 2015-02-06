#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    module will hold functions to generate reports either to STDOUT or html
'''

import os

from garmin_utils import print_date_string, print_h_m_s, run_command,\
    METERS_PER_MILE, MARATHON_DISTANCE_MI

class GarminReport(object):
    '''
        Class to produce reports, to stdout, and to html
        Reports are for:
            individual files
            summaries of files, days, weeks, months and years
    '''
    def __init__(self):
        self.report_type = ''

    def file_report_txt(self, gfile):
        ''' nice output string for a file '''
        retval = ['Start time %s' % print_date_string(gfile.begin_datetime)]

        for lap in gfile.laps:
            retval.append(print_lap_string(lap, gfile.sport))

        min_mile = 0
        mi_per_hr = 0
        if gfile.total_distance > 0:
            min_mile = (gfile.total_duration / 60.) / (gfile.total_distance / METERS_PER_MILE)
        if gfile.total_duration > 0:
            mi_per_hr = (gfile.total_distance / METERS_PER_MILE) / (gfile.total_duration/60./60.)

        tmpstr = []
        if gfile.sport == 'running':
            tmpstr.append('total %.2f mi %s calories %s time %s min/mi %s min/km' % (gfile.total_distance / METERS_PER_MILE, gfile.total_calories, print_h_m_s(gfile.total_duration), print_h_m_s(min_mile*60, False), print_h_m_s(min_mile*60 / METERS_PER_MILE * 1000., False)))
        else:
            tmpstr.append('total %.2f mi %s calories %s time %.2f mph' % (gfile.total_distance / METERS_PER_MILE, gfile.total_calories, print_h_m_s(gfile.total_duration), mi_per_hr))
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
            if point.heart_rate > 0:
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
            if point.altitude > 0:
                alt_vals.append(point.altitude)
                if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2]:
                    vertical_climb += alt_vals[-1] - alt_vals[-2]
        if len(alt_vals) > 0:
            retval.append('max altitude diff: %.2f m' % (max(alt_vals) - min(alt_vals)))
            retval.append('vertical climb: %.2f m' % vertical_climb)
        retval.append('')

        return '\n'.join(retval)
    
    def file_report_html(self, gfile, use_time=False, **options):
        ''' create pretty plots '''
        avg_hr = 0
        sum_time = 0
        max_hr = 0
        hr_vals = []
        hr_values = []
        alt_vals = []
        alt_values = []
        vertical_climb = 0
        speed_values = filter(lambda x: x[1] < 20, [[d/4., 4*t/60.] for d, t in get_splits(gfile, 400., do_heart_rate=False)])
        mph_speed_values = []
        avg_speed_values = []
        avg_mph_speed_values = []
        lat_vals = []
        lon_vals = []
        graphs = []
        mile_split_vals = [[d, t/60.] for d, t in get_splits(gfile, METERS_PER_MILE, do_heart_rate=False)]
        for point in gfile.points:
            if use_time:
                xval = point.duration_from_begin
            else:
                xval = point.distance / METERS_PER_MILE
            if xval > 0 and point.heart_rate > 0:
                avg_hr += point.heart_rate * point.duration_from_last
                sum_time += point.duration_from_last
                hr_vals.append(point.heart_rate)
                hr_values.append([xval, point.heart_rate])
            if point.altitude > 0:
                alt_vals.append(point.altitude)
                if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2]:
                    vertical_climb += alt_vals[-1] - alt_vals[-2]
                alt_values.append([xval, point.altitude])
            # if point.speed_permi > 0 and point.speed_permi < 20:
                # speed_values.append([xval, point.speed_permi])
            if point.speed_mph > 0 and point.speed_mph < 20:
                mph_speed_values.append([xval, point.speed_mph])
            if point.avg_speed_value_permi > 0 and point.avg_speed_value_permi < 20:
                avg_speed_values.append([xval, point.avg_speed_value_permi])
            if point.avg_speed_value_mph > 0:
                avg_mph_speed_values.append([xval, point.avg_speed_value_mph])
            if point.latitude and point.longitude:
                lat_vals.append(point.latitude)
                lon_vals.append(point.longitude)
        if sum_time > 0:
            avg_hr /= sum_time
            max_hr = max(hr_vals)

        #if len(hr_vals) > 0:
            #print 'Heart Rate %2.2f avg %2.2f max' % (avg_hr, max(hr_vals))

        #if len(alt_vals) > 0:
            #print 'max altitude diff: %.2f m' % (max(alt_vals) - min(alt_vals))
            #print 'vertical climb: %.2f m' % vertical_climb

        curpath = options['script_path']
        #print curpath
        if not os.path.exists('%s/html' % curpath):
            os.makedirs('%s/html' % curpath)
        #os.chdir('%s/html' % curpath)

        if len(mile_split_vals) > 0:
            options = {'plotopt': {'marker': 'o'}}
            graphs.append(plot_graph(name='mile_splits', title='Pace per Mile every mi', data=mile_split_vals, **options))

        if len(hr_values) > 0:
            graphs.append(plot_graph(name='heart_rate', title='Heart Rate %2.2f avg %2.2f max' % (avg_hr, max_hr), data=hr_values))
        if len(alt_values) > 0:
            graphs.append(plot_graph(name='altitude', title='Altitude', data=alt_values))
        if len(speed_values) > 0:
            graphs.append(plot_graph(name='speed_minpermi', title='Speed min/mi every 1/4 mi', data=speed_values))
            graphs.append(plot_graph(name='speed_mph', title='Speed mph', data=mph_speed_values))

        if len(avg_speed_values) > 0:
            avg_speed_value_min = int(avg_speed_values[-1][1])
            avg_speed_value_sec = int((avg_speed_values[-1][1] - avg_speed_value_min) * 60.)
            graphs.append(plot_graph(name='avg_speed_minpermi', title='Avg Speed %i:%02i min/mi' % (avg_speed_value_min, avg_speed_value_sec), data=avg_speed_values))

        if len(avg_mph_speed_values) > 0:
            avg_mph_speed_value = avg_mph_speed_values[-1][1]
            graphs.append(plot_graph(name='avg_speed_mph', title='Avg Speed %.2f mph' % avg_mph_speed_value, data=avg_mph_speed_values))

        with open('html/index.html', 'w') as htmlfile:
            if len(lat_vals) > 0 and len(lon_vals) > 0 and len(lat_vals) == len(lon_vals):
                minlat, maxlat = min(lat_vals), max(lat_vals)
                minlon, maxlon = min(lon_vals), max(lon_vals)
                central_lat = (maxlat + minlat)/2.
                central_lon = (maxlon + minlon)/2.
                latlon_min = max((maxlat-minlat), (maxlon-minlon))
                print 'latlon', latlon_min
                latlon_thresholds = [[15, 0.015], [14, 0.038], [13, 0.07], [12, 0.12], [11, 0.20], [10, 0.4]]
                for line in open('%s/MAP_TEMPLATE.html' % curpath, 'r'):
                    if 'SPORTTITLEDATE' in line:
                        newtitle = 'Garmin Event %s on %s' % (gfile.sport.title(), gfile.begin_datetime)
                        htmlfile.write(line.replace('SPORTTITLEDATE',newtitle))
                    elif 'ZOOMVALUE' in line:
                        for zoom, thresh in latlon_thresholds:
                            if latlon_min < thresh or zoom == 10:
                                htmlfile.write(line.replace('ZOOMVALUE','%d' % zoom))
                                break
                    elif 'INSERTTABLESHERE' in line:
                        htmlfile.write('%s\n' % get_file_html(gfile))
                        htmlfile.write('<br><br>%s\n' % get_html_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi'))
                        htmlfile.write('<br><br>%s\n' % get_html_splits(gfile, split_distance_in_meters=5000., label='km'))
                    elif 'INSERTMAPSEGMENTSHERE' in line:
                        for idx in range(0, len(lat_vals)):
                            htmlfile.write('new google.maps.LatLng(%f,%f),\n' % (lat_vals[idx], lon_vals[idx]))
                    elif 'MINLAT' in line or 'MAXLAT' in line or 'MINLON' in line or 'MAXLON' in line:
                        htmlfile.write(line.replace('MINLAT', '%s' % minlat).replace('MAXLAT', '%s' % maxlat).replace('MINLON', '%s' % minlon).replace('MAXLON', '%s' % maxlon))
                    elif 'CENTRALLAT' in line or 'CENTRALLON' in line:
                        htmlfile.write(line.replace('CENTRALLAT', '%s' % central_lat).replace('CENTRALLON', '%s' % central_lon))
                    elif 'INSERTOTHERIMAGESHERE' in line:
                        for f in graphs:
                            htmlfile.write('<p>\n<img src="%s">\n</p>' % f)
                    else:
                        htmlfile.write(line)
            else:
                htmlfile.write('<!DOCTYPE HTML>\n<html>\n<body>\n')

        os.chdir(curpath)
        if os.path.exists('%s/html' % curpath) and os.path.exists('%s/public_html/garmin' % os.getenv('HOME')):
            if os.path.exists('%s/public_html/garmin/html' % os.getenv('HOME')):
                run_command('rm -rf %s/public_html/garmin/html' % os.getenv('HOME'))
            run_command('mv %s/html %s/public_html/garmin' % (curpath, os.getenv('HOME')))


def print_lap_string(glap, sport):
    ''' print nice output for a lap '''
    outstr = ['%s lap %i %.2f mi %s %s calories %.2f min' % (sport, glap.lap_number, glap.lap_distance / METERS_PER_MILE, print_h_m_s(glap.lap_duration), glap.lap_calories, glap.lap_duration / 60.)]
    if sport == 'running':
        if glap.lap_distance > 0:
            outstr.extend([print_h_m_s(glap.lap_duration / (glap.lap_distance / METERS_PER_MILE), False), '/ mi ',
                           print_h_m_s(glap.lap_duration / (glap.lap_distance / 1000.), False), '/ km',])
    if glap.lap_avg_hr > 0:
        outstr.append('%i bpm' % glap.lap_avg_hr)

    return ' '.join(outstr)

def get_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi', do_heart_rate=True):
    ''' get splits for given split distance '''
    if len(gfile.points) == 0: return None
    last_point_me = 0
    last_point_time = 0
    prev_split_me = 0
    prev_split_time = 0
    avg_hrt_rate = 0
    split_vector = []

    for point in gfile.points:
        cur_point_me = point.distance
        cur_point_time = point.duration_from_begin
        if (cur_point_me - last_point_me) <= 0:
            continue
        if point.heart_rate:
            try:
                avg_hrt_rate += point.heart_rate * (cur_point_time - last_point_time)
            except Exception as exc:
                print 'Exception:', exc, point.heart_rate, cur_point_time, last_point_me
                exit(0)
        nmiles = int(cur_point_me/split_distance_in_meters) - int(last_point_me/split_distance_in_meters)
        if nmiles > 0:
            cur_split_me = int(cur_point_me/split_distance_in_meters)*split_distance_in_meters
            cur_split_time = last_point_time + (cur_point_time - last_point_time) / (cur_point_me - last_point_me) * (cur_split_me - last_point_me)
            time_val = (cur_split_time - prev_split_time)
            split_dist = cur_point_me/split_distance_in_meters
            if label == 'km':
                split_dist = cur_point_me/1000.

            tmp_vector = [split_dist, time_val]
            if do_heart_rate:
                tmp_vector.append(avg_hrt_rate / (cur_split_time - prev_split_time))
            split_vector.append(tmp_vector)

            prev_split_me = cur_split_me
            prev_split_time = cur_split_time
            avg_hrt_rate = 0
        last_point_me = cur_point_me
        last_point_time = cur_point_time

    return split_vector

def print_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi', print_out=True):
    ''' print split time for given split distance '''
    if len(gfile.points) == 0: return None

    retval = []
    split_vector = get_splits(gfile, split_distance_in_meters, label)
    for d, t, h in split_vector:
        retval.append('%i %s \t %s \t %s / mi \t %s / km \t %s \t %i bpm avg'
            % (d,
               label,
               print_h_m_s(t),
               print_h_m_s(t/(split_distance_in_meters/METERS_PER_MILE), False),
               print_h_m_s(t/(split_distance_in_meters/1000.), False),
               print_h_m_s(
                   t/(split_distance_in_meters/METERS_PER_MILE)
                   *MARATHON_DISTANCE_MI),
               h)
           )
    return '\n'.join(retval)

def plot_graph(name=None, title=None, data=None, **opts):
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl
    
    popts = {}
    if 'plotopt' in opts:
        popts = opts['plotopt']
    pl.clf()
    x, y = zip(*data)
    xa = np.array(x)
    ya = np.array(y)
    pl.plot(xa, ya, **popts)
    xmin, xmax, ymin, ymax = pl.axis()
    xmin, ymin = map(lambda z: z - 0.1 * abs(z), [xmin, ymin])
    xmax, ymax = map(lambda z: z + 0.1 * abs(z), [xmax, ymax])
    pl.axis([xmin, xmax, ymin, ymax])
    pl.title(title)
    pl.savefig('html/%s.png' % name)
    return '%s.png' % name

def get_file_html(gfile):
    ''' nice output html for a file '''
    retval = []
    retval.append('<table border="1" class="dataframe">')
    retval.append('<thead><tr style="text-align: center;"><th>Start Time</th><th>Sport</th></tr></thead>')
    retval.append('<tbody><tr style="text-align: center;"><td>%s</td><td>%s</td></tr></tbody>' % (print_date_string(gfile.begin_datetime), gfile.sport))
    retval.append('</table><br>')

    labels = ['Sport', 'Lap', 'Distance', 'Duration', 'Calories', 'Time', 'Pace / mi', 'Pace / km', 'Heart Rate']
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
        mi_per_hr = (gfile.total_distance / METERS_PER_MILE) / (gfile.total_duration/60./60.)

    if gfile.sport == 'running':
        labels = ['', 'Distance', 'Calories', 'Time', 'Pace / mi', 'Pace / km']
        values = ['total',
                  '%.2f mi' % (gfile.total_distance/METERS_PER_MILE),
                  gfile.total_calories,
                  print_h_m_s(gfile.total_duration),
                  print_h_m_s(min_mile*60, False),
                  print_h_m_s(min_mile*60/METERS_PER_MILE*1000., False)
               ]
    else:
        labels = ['total', 'Disatnce', 'Calories', 'Time', 'Pace mph']
        values = ['',
                  '%.2f mi' % (gfile.total_distance/METERS_PER_MILE),
                  gfile.total_calories,
                  print_h_m_s(gfile.total_duration),
                  mi_per_hr
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

    values = [sport,
              glap.lap_number,
              '%.2f mi' % (glap.lap_distance/METERS_PER_MILE),
              print_h_m_s(glap.lap_duration),
              glap.lap_calories,
              '%.2f min' % (glap.lap_duration/60.),
              '%s / mi' % print_h_m_s(glap.lap_duration / (glap.lap_distance / METERS_PER_MILE), False),
              '%s / km' % print_h_m_s(glap.lap_duration / (glap.lap_distance / 1000.), False),
              '%i bpm' % glap.lap_avg_hr
            ]

    return ['<td>%s</td>' % v for v in values]

def get_html_splits(gfile, split_distance_in_meters=METERS_PER_MILE, label='mi'):
    ''' print split time for given split distance '''
    if len(gfile.points) == 0: return None

    labels = ['Split', 'Time', 'Pace / mi', 'Pace / km', 'Marathon Time', 'Heart Rate']
    values = []

    split_vector = get_splits(gfile, split_distance_in_meters, label)
    for d, t, h in split_vector:
        tmp_vector = [
                        '%i %s' % (d, label),
                        print_h_m_s(t),
                        print_h_m_s(t/(split_distance_in_meters/METERS_PER_MILE), False),
                        print_h_m_s(t/(split_distance_in_meters/1000.), False),
                        print_h_m_s(t/(split_distance_in_meters/METERS_PER_MILE)*MARATHON_DISTANCE_MI),
                        '%i bpm' % h
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
