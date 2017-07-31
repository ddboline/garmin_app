# -*- coding: utf-8 -*-
"""
    parsers to read txt, xml, tcx formatted files
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
try:
    from itertools import izip
except ImportError:
    from builtins import zip as izip
import datetime

from garmin_app.garmin_file import GarminFile
from garmin_app.garmin_lap import GarminLap
from garmin_app.garmin_point import GarminPoint
from garmin_app.garmin_utils import (METERS_PER_MILE, convert_time_string, print_date_string,
                                     convert_fit_to_tcx, convert_gmn_to_xml, expected_calories,
                                     convert_date_string)
from garmin_app.garmin_corrections import LIST_OF_MISLABELED_TIMES

from garmin_app.util import (run_command, haversine_distance)


class GarminParse(GarminFile):
    """
        Parse garmin xml based formats
    """

    def __init__(self, filename, filetype='', corr_list=None):
        """ Init Method """
        GarminFile.__init__(self, filename, filetype)

        if filetype in GarminFile.garmin_file_types:
            self.filetype = filetype
        else:
            self._determine_file_type()
        self.corr_list = []
        if corr_list:
            self.corr_list = corr_list

    def __del__(self):
        if hasattr(self, 'filetype') and \
                self.filetype in ('fit', 'gmn') \
                and os.path.exists(self.orig_filename):
            os.remove(self.orig_filename)

    def _determine_file_type(self):
        """ determine file type """
        if '.tcx' in self.orig_filename.lower():
            self.filetype = 'tcx'
        elif '.txt' in self.orig_filename.lower():
            self.filetype = 'txt'
        elif '.fit' in self.orig_filename.lower():
            self.orig_filename = convert_fit_to_tcx(self.orig_filename)
            self.filetype = 'fit'
        elif '.gmn' in self.orig_filename.lower():
            self.filetype = 'gmn'
            self.orig_filename = convert_gmn_to_xml(self.orig_filename)
        elif '.gpx' in self.orig_filename.lower():
            self.filetype = 'gpx'

    def read_file(self):
        """ read file, use is_tcx/is_txt to decide which function to call """
        if self.filetype == 'tcx' or self.filetype == 'fit':
            self.read_file_tcx()
        elif self.filetype == 'txt':
            self.read_file_txt()
        elif self.filetype == 'gmn':
            self.read_file_xml()
        elif self.filetype == 'gpx':
            self.read_file_gpx()
        if len(self.laps) > 0:
            self.begin_datetime = self.laps[0].lap_start
        elif len(self.points) > 0:
            self.begin_datetime = self.points[0].time
        else:
            self.begin_datetime = datetime.datetime.now()
        printed_datetime = print_date_string(self.begin_datetime)
        for sport in LIST_OF_MISLABELED_TIMES:
            if printed_datetime in LIST_OF_MISLABELED_TIMES[sport]:
                self.sport = sport
        self.calculate_speed()

    def read_file_xml(self):
        """ read xml file """
        cur_lap = None
        cur_point = None
        last_ent = None
        temp_points = []
        with run_command('xml2 < %s' % self.orig_filename, do_popen=True) as pop_:
            for line in pop_:
                if hasattr(line, 'decode'):
                    line = line.decode()
                ent = line.strip().split('/')
                if ent[2] == 'run':
                    if '@sport' in ent[3]:
                        self.sport = ent[3].split('=')[1]
                elif ent[2] == 'lap':
                    if len(ent) < 4:
                        self.laps.append(cur_lap)
                    elif 'type' in ent[3]:
                        cur_lap = GarminLap()
                    cur_lap.read_lap_xml(ent[3:])
                elif ent[2] == 'point':
                    if len(ent) < 4:
                        temp_points.append(cur_point)
                    elif 'type' in ent[3]:
                        cur_point = GarminPoint()
                    cur_point.read_point_xml(ent[3:])
                else:
                    pass
                if ent[2] != 'lap' and last_ent and last_ent[2] == 'lap':
                    self.laps.append(cur_lap)
                last_ent = ent
        if cur_lap and cur_lap not in self.laps:
            self.laps.append(cur_lap)
        if cur_point and cur_point not in temp_points:
            temp_points.append(cur_point)
        corrected_laps = {}
        lstr_ = print_date_string(self.laps[0].lap_start)
        if lstr_ in self.corr_list:
            corrected_laps = self.corr_list[lstr_]
        for lap_number, cur_lap in enumerate(self.laps):
            if lap_number in corrected_laps:
                if type(corrected_laps[lap_number]) == float\
                        or len(corrected_laps[lap_number]) == 1:
                    cur_lap.lap_distance = (corrected_laps[lap_number] * METERS_PER_MILE)
                else:
                    cur_lap.lap_distance = (corrected_laps[lap_number][0] * METERS_PER_MILE)
                    cur_lap.lap_duration = corrected_laps[lap_number][1]

            cur_lap.lap_number = lap_number
            self.total_distance += cur_lap.lap_distance
            self.total_calories += cur_lap.lap_calories
            self.total_duration += cur_lap.lap_duration
            if cur_lap.lap_avg_hr:
                self.total_hr_dur += cur_lap.lap_avg_hr * cur_lap.lap_duration
                self.total_hr_dis += cur_lap.lap_duration

        time_from_begin = 0
        for point_number, cur_point in enumerate(temp_points):
            if point_number == 0:
                cur_point.duration_from_last = 0.
            else:
                cur_point.duration_from_last = ((cur_point.time - temp_points[point_number - 1]
                                                 .time).total_seconds())
            time_from_begin += cur_point.duration_from_last
            cur_point.duration_from_begin = time_from_begin

            if cur_point.distance and cur_point.distance > 0:
                self.points.append(cur_point)

        printed_datetime = print_date_string(self.laps[0].lap_start)
        for sport in LIST_OF_MISLABELED_TIMES:
            if printed_datetime in LIST_OF_MISLABELED_TIMES[sport]:
                self.sport = sport
                if self.sport == 'biking':
                    self.total_calories = int(self.total_calories * (1701 / 26.26) / (3390 / 26.43))
                    for lap in self.laps:
                        lap.lap_calories = int(lap.lap_calories * (1701 / 26.26) / (3390 / 26.43))
                if self.sport == 'running':
                    self.total_calories = int(self.total_calories * (3390 / 26.43) / (1701 / 26.26))
                    for lap in self.laps:
                        lap.lap_calories = int(lap.lap_calories * (3390 / 26.43) / (1701 / 26.26))

    def read_file_gpx(self):
        lats = []
        lons = []
        eles = []
        times = []
        with run_command('xml2 < %s' % self.orig_filename, do_popen=True) as pop_:
            for idx, line in enumerate(pop_):
                if hasattr(line, 'decode'):
                    line = line.decode()
                ent = line.strip().split('/')
                if len(ent) == 6 and 'lat' in ent[5]:
                    lats.append(float(ent[5].split('=')[-1]))
                if len(ent) == 6 and 'lon' in ent[5]:
                    lons.append(float(ent[5].split('=')[-1]))
                if len(ent) == 6 and 'ele' in ent[5]:
                    eles.append(float(ent[5].split('=')[-1]))
                if len(ent) == 6 and 'time' in ent[5]:
                    times.append(convert_date_string(ent[5].split('=')[-1]))
        assert len(lats) == len(lons)
        if not eles:
            eles = [0 for _ in range(len(lats))]
        last = None
        last_alt = 0
        distance = 0
        for lat, lon, ele, time in zip(lats, lons, eles, times):
            cur_point = GarminPoint()
            cur_point.latitude = lat
            cur_point.longitude = lon
            if ele > 10000:
                ele = last_alt
            else:
                last_alt = ele
            cur_point.altitude = ele
            
            cur_point.time = time
            if last is not None:
                distance += haversine_distance(lat, lon, last[0], last[1])
            cur_point.distance = distance
            last = (lat, lon)
            self.points.append(cur_point)
        self.sport = 'running'

    def read_file_tcx(self):
        """ read tcx file """
        cur_lap = None
        cur_point = None
        temp_points = []
        with run_command('xml2 < %s' % self.orig_filename, do_popen=True) as pop_:
            for line in pop_:
                if hasattr(line, 'decode'):
                    line = line.decode()
                ent = line.strip().split('/')
                if len(ent) < 5:
                    continue
                elif 'Sport' in ent[4]:
                    self.sport = ent[4].split('=')[1].lower()
                elif ent[4] == 'Lap':
                    if len(ent[5:]) == 0:
                        self.laps.append(cur_lap)
                    elif 'StartTime' in ent[5]:
                        cur_lap = GarminLap()
                    elif ent[5] == 'Track':
                        if len(ent[6:]) == 0:
                            continue
                        elif ent[6] == 'Trackpoint':
                            if len(ent[7:]) == 0:
                                temp_points.append(cur_point)
                            elif 'Time' in ent[7]:
                                cur_point = GarminPoint()
                            cur_point.read_point_tcx(ent[7:])
                    cur_lap.read_lap_tcx(ent[5:])

        if cur_lap not in self.laps:
            self.laps.append(cur_lap)
        if cur_point not in temp_points:
            temp_points.append(cur_point)

        corrected_laps = {}
        lstr_ = print_date_string(self.laps[0].lap_start)
        if lstr_ in self.corr_list:
            corrected_laps = self.corr_list[lstr_]
        for lap_number, cur_lap in enumerate(self.laps):
            if lap_number in corrected_laps:
                if type(corrected_laps[lap_number]) in [float, int]:
                    cur_lap.lap_distance = (corrected_laps[lap_number] * METERS_PER_MILE)
                elif type(corrected_laps[lap_number]) == list:
                    cur_lap.lap_distance = (corrected_laps[lap_number][0] * METERS_PER_MILE)
                    cur_lap.lap_duration = corrected_laps[lap_number][1]
            cur_lap.lap_number = lap_number
            self.total_distance += cur_lap.lap_distance
            self.total_calories += cur_lap.lap_calories
            self.total_duration += cur_lap.lap_duration
            if cur_lap.lap_avg_hr:
                self.total_hr_dur += cur_lap.lap_avg_hr * cur_lap.lap_duration
                self.total_hr_dis += cur_lap.lap_duration

        time_from_begin = 0
        for point_number, cur_point in enumerate(temp_points):
            if point_number == 0:
                cur_point.duration_from_last = 0.
            else:
                cur_point.duration_from_last = ((cur_point.time - temp_points[point_number - 1]
                                                 .time).total_seconds())
            time_from_begin += cur_point.duration_from_last
            cur_point.duration_from_begin = time_from_begin

            self.points.append(cur_point)

    def read_file_txt(self):
        """ read txt file, these just contain summary information """
        with open(self.orig_filename, 'rt') as infile:
            for line in infile:
                if len(line.strip()) == 0:
                    continue
                cur_lap = None
                cur_point = None

                for ent in line.strip().split():
                    if '=' not in ent:
                        continue
                    key = ent.split('=')[0]
                    val = ent.split('=')[1]
                    if key == 'date':
                        year = int(val[0:4])
                        month = int(val[4:6])
                        day = int(val[6:8])
                        if not cur_lap:
                            cur_lap = GarminLap()
                        if not cur_point:
                            cur_point = GarminPoint()
                        cur_lap.lap_start = datetime.datetime(year, month, day)
                        cur_point.time = datetime.datetime(year, month, day)
                        if len(self.points) == 0:
                            self.points.append(cur_point)
                            cur_point = GarminPoint(time=cur_point.time)
                    if key == 'time':
                        year, month, day = (cur_lap.lap_start.year, cur_lap.lap_start.month,
                                            cur_lap.lap_start.day)
                        hour, minute, second = [int(x) for x in val.split(':')[:3]]

                        cur_lap.lap_start = datetime.datetime(
                            year=year,
                            month=month,
                            day=day,
                            hour=hour,
                            minute=minute,
                            second=second)
                    if key == 'type':
                        self.sport = val
                    if key == 'lap':
                        cur_lap.lap_number = int(val)
                    if key == 'dur':
                        cur_lap.lap_duration = float(convert_time_string(val))
                        cur_point.time = (
                            self.points[-1].time + datetime.timedelta(seconds=cur_lap.lap_duration))
                    if key == 'dis':
                        if 'mi' in val:  # specify mi, m or assume it's meters
                            cur_lap.lap_distance = (float(val.split('mi')[0]) * METERS_PER_MILE)
                        elif 'm' in val:
                            cur_lap.lap_distance = float(val.split('m')[0])
                        else:
                            cur_lap.lap_distance = float(val)
                        cur_point.distance = cur_lap.lap_distance
                        if self.points[-1].distance:
                            cur_point.distance += self.points[-1].distance
                    if key == 'cal':
                        cur_lap.lap_calories = int(val)
                    if key == 'avghr':
                        cur_lap.lap_avg_hr = float(val)
                        cur_point.heart_rate = cur_lap.lap_avg_hr
                if cur_lap.lap_calories == -1:
                    dur = cur_lap.lap_duration / 60.
                    dis = cur_lap.lap_distance / METERS_PER_MILE
                    pace = dur / dis
                    cur_lap.lap_calories = int(
                        expected_calories(weight=175, pace_min_per_mile=pace, distance=dis))
                self.total_calories += cur_lap.lap_calories
                self.total_distance += cur_lap.lap_distance
                self.total_duration += cur_lap.lap_duration
                if cur_lap.lap_avg_hr:
                    self.total_hr_dur += (cur_lap.lap_avg_hr * cur_lap.lap_duration)
                    self.total_hr_dis += cur_lap.lap_duration
                self.laps.append(cur_lap)
                self.points.append(cur_point)

        time_since_begin = 0
        for point0, point1 in izip(self.points[1:], self.points):
            if point0.distance and point1.distance and \
                    point0.distance > point1.distance:
                point0.duration_from_last = ((point0.time - point1.time).total_seconds())
                time_since_begin += point0.duration_from_last
                point0.duration_from_begin = time_since_begin
            else:
                point0.duration_from_last = 0
