# -*- coding: utf-8 -*-
"""
    module holds classes:
        GarminPoint
        GarminLap
        GarminFile
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from garmin_app.garmin_utils import convert_date_string, convert_time_string,\
    METERS_PER_MILE

class GarminPoint(object):
    """
        point representing each gps point
    """
    __slots__ = ['time', 'latitude', 'longitude', 'altitude', 'distance',
                 'heart_rate', 'duration_from_last', 'duration_from_begin',
                 'speed_mps', 'speed_permi', 'speed_mph',
                 'avg_speed_value_permi', 'avg_speed_value_mph']

    def __init__(self, **options):
        for attr in self.__slots__:
            if attr in options:
                setattr(self, attr, options[attr])
            else:
                setattr(self, attr, None)
        self.duration_from_last = 0 ### keep a running total for convenience
        self.duration_from_begin = 0 ### keep a running total for convenience
        self.speed_mps = 0
        self.speed_permi = -1
        self.speed_mph = 0
        self.avg_speed_value_permi = -1
        self.avg_speed_value_mph = 0


    def __repr__(self):
        return 'GarminPoint<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__)

    def read_point_xml(self, ent):
        for e in ent:
            if '@time' in e:
                self.time = convert_date_string(e.split('=')[1])
            elif '@lat' in e:
                self.latitude = float(e.split('=')[1])
            elif '@lon' in e:
                self.longitude = float(e.split('=')[1])
            elif '@alt' in e:
                self.altitude = float(e.split('=')[1])
            elif '@distance' in e:
                self.distance = float(e.split('=')[1])
            elif '@hr' in e:
                self.heart_rate = float(e.split('=')[1])

    def read_point_tcx(self, ent):
        if len(ent) > 0:
            if 'Time' in ent[0]:
                self.time = convert_date_string(ent[0].split('=')[1])
            elif 'Position' in ent[0]:
                if 'LatitudeDegrees' in ent[1]:
                    self.latitude = float(ent[1].split('=')[1])
                elif 'LongitudeDegrees' in ent[1]:
                    self.longitude = float(ent[1].split('=')[1])
            elif 'AltitudeMeters' in ent[0]:
                self.altitude = float(ent[0].split('=')[1])
            elif 'DistanceMeters' in ent[0]:
                self.distance = float(ent[0].split('=')[1])
            elif 'HeartRateBpm' in ent[0]:
                if 'Value' in ent[1]:
                    self.heart_rate = int(ent[1].split('=')[1])
            elif 'Extensions' in ent[0]:
                if len(ent) > 2:
                    if 'Speed' in ent[2]:
                        self.speed_mps = float(ent[2].split('=')[1])
                        self.speed_mph = self.speed_mps * 3600.\
                                         / METERS_PER_MILE
                        if self.speed_mps > 0.:
                            self.speed_permi = METERS_PER_MILE\
                                               / self.speed_mps / 60.

class GarminLap(object):
    """
        class representing each lap in xml file
            functions:
                read_lap_xml(node), read_lap_tcx(node), print_lap_string(node)
    """
    __slots__ = ['lap_type', 'lap_index', 'lap_start', 'lap_duration',
                 'lap_distance', 'lap_trigger', 'lap_max_speed',
                 'lap_calories', 'lap_avg_hr', 'lap_max_hr', 'lap_intensity',
                 'lap_number', 'lap_start_string']

    def __init__(self, **options):
        for attr in self.__slots__:
            if attr in options:
                setattr(self, attr, options[attr])
            else:
                setattr(self, attr, None)

    def __repr__(self):
        return 'GarminLap<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__)

    def read_lap_xml(self, ent):
        """ read lap from xml file """
        for e in ent:
            if 'type' in e:
                self.lap_type = e.split('=')[1]
            elif 'index' in e:
                self.lap_index = int(e.split('=')[1])
            elif 'start' in e:
                self.lap_start_string = e.split('=')[1]
                self.lap_start = convert_date_string(self.lap_start_string)
            elif 'duration' in e:
                self.lap_duration = float(convert_time_string(e.split('=')[1]))
            elif 'distance' in e:
                self.lap_distance = float(e.split('=')[1])
            elif 'trigger' in e:
                self.lap_trigger = e.split('=')[1]
            elif 'max_speed' in e:
                self.lap_max_speed = float(e.split('=')[1])
            elif 'calories' in e:
                self.lap_calories = int(e.split('=')[1])
            elif 'avg_hr' in e:
                self.lap_avg_hr = int(e.split('=')[1])
            elif 'max_hr' in e:
                self.lap_max_hr = int(e.split('=')[1])
            elif 'intensity' in e:
                self.lap_intensity = e.split('=')[1]
            else:
                continue

    def read_lap_tcx(self, ent):
        if len(ent) > 0:
            if 'StartTime' in ent[0]:
                self.lap_start_string = ent[0].split('=')[1]
                self.lap_start = convert_date_string(self.lap_start_string)
            elif 'TotalTimeSeconds' in ent[0]:
                self.lap_duration = float(ent[0].split('=')[1])
            elif 'DistanceMeters' in ent[0]:
                self.lap_distance = float(ent[0].split('=')[1])
            elif 'TriggerMethod' in ent[0]:
                self.lap_trigger = ent[0].split('=')[1]
            elif 'MaximumSpeed' in ent[0]:
                self.lap_max_speed = float(ent[0].split('=')[1])
            elif 'Calories' in ent[0]:
                self.lap_calories = int(ent[0].split('=')[1])
            elif 'AverageHeartRateBpm' in ent[0]:
                if 'Value' in ent[1]:
                    self.lap_avg_hr = int(ent[1].split('=')[1])
            elif 'MaximumHeartRateBpm' in ent[0]:
                if 'Value' in ent[1]:
                    self.lap_max_hr = int(ent[1].split('=')[1])
            elif 'Intensity' in ent[0]:
                self.lap_intensity = ent[0].split('=')[1]
        return None


class GarminFile(object):
    """
        class representing a full xml file
            functions:
                read_file(), read_file_tcx(), read_file_xml(),
                print_file_string(), calculate_speed(), print_splits()
    """
    __slots__ = ['filename', 'orig_filename', 'filetype', 'begin_datetime',
                 'sport', 'total_calories', 'total_distance', 'total_duration',
                 'total_hr_dur', 'total_hr_dis', 'laps', 'points']
    garmin_file_types = ('txt', 'tcx', 'fit', 'gpx', 'gmn')

    def __init__(self, filename='', filetype=''):
        self.orig_filename = filename
        self.filename = filename
        self.filetype = ''
        if filetype in self.garmin_file_types:
            self.filetype = filetype
        self.begin_datetime = None
        self.sport = None
        self.total_calories = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_hr_dur = 0
        self.total_hr_dis = 0
        self.laps = []
        self.points = []

    def __repr__(self):
        return 'GarminFile<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__
                                            if x not in ['points', 'laps'])

    def calculate_speed(self):
        """
            calculate instantaneous speed (could maybe be a bit more elaborate)
        """
        for idx in range(1, len(self.points)):
            jdx = idx - 1
            t1 = self.points[idx].time
            t0 = self.points[jdx].time
            d1 = self.points[idx].distance
            d0 = self.points[jdx].distance
            if any([x == None for x in [t1, t0, d1, d0]]):
                continue
            totdur = (t1 - t0).total_seconds() # seconds
            totdis = d1 - d0 # meters
            if totdis > 0 and not self.points[idx].speed_permi:
                self.points[idx].speed_permi = (totdur/60.)\
                                                / (totdis/METERS_PER_MILE)
            if totdur > 0 and not self.points[idx].speed_mph:
                self.points[idx].speed_mph = (totdis/METERS_PER_MILE)\
                                              / (totdur/60./60.)
            if totdur > 0 and not self.points[idx].speed_mps:
                self.points[idx].speed_mps = totdis / totdur
            if d1 > 0:
                self.points[idx].avg_speed_value_permi = \
                    ((t1 - self.points[0].time).total_seconds()/60.)\
                     / (d1/METERS_PER_MILE)
            if (t1 - self.points[0].time).total_seconds() > 0:
                self.points[idx].avg_speed_value_mph = \
                    (self.points[idx].distance/METERS_PER_MILE)\
                     / ((t1 - self.points[0].time).total_seconds()/60./60.)
        return None
