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

from garmin_app.garmin_utils import (convert_date_string, convert_time_string,
                                     METERS_PER_MILE)

class GarminPoint(object):
    """
        point representing each gps point
    """
    __slots__ = ['time', 'latitude', 'longitude', 'altitude', 'distance',
                 'heart_rate', 'duration_from_last', 'duration_from_begin',
                 'speed_mps', 'speed_permi', 'speed_mph',
                 'avg_speed_value_permi', 'avg_speed_value_mph']

    def __init__(self, **options):
        """ Init Method """
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
        """ string representation """
        return 'GarminPoint<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__)

    def read_point_xml(self, ents):
        """ read xml point """
        for ent in ents:
            if '@time' in ent:
                self.time = convert_date_string(ent.split('=')[1])
            elif '@lat' in ent:
                self.latitude = float(ent.split('=')[1])
            elif '@lon' in ent:
                self.longitude = float(ent.split('=')[1])
            elif '@alt' in ent:
                self.altitude = float(ent.split('=')[1])
            elif '@distance' in ent:
                self.distance = float(ent.split('=')[1])
            elif '@hr' in ent:
                self.heart_rate = float(ent.split('=')[1])

    def read_point_tcx(self, ents):
        """ read tcx point """
        if len(ents) > 0:
            if 'Time' in ents[0]:
                self.time = convert_date_string(ents[0].split('=')[1])
            elif 'Position' in ents[0]:
                if 'LatitudeDegrees' in ents[1]:
                    self.latitude = float(ents[1].split('=')[1])
                elif 'LongitudeDegrees' in ents[1]:
                    self.longitude = float(ents[1].split('=')[1])
            elif 'AltitudeMeters' in ents[0]:
                self.altitude = float(ents[0].split('=')[1])
            elif 'DistanceMeters' in ents[0]:
                self.distance = float(ents[0].split('=')[1])
            elif 'HeartRateBpm' in ents[0]:
                if 'Value' in ents[1]:
                    self.heart_rate = int(ents[1].split('=')[1])
            elif 'Extensions' in ents[0]:
                if len(ents) > 2:
                    if 'Speed' in ents[2]:
                        self.speed_mps = float(ents[2].split('=')[1])
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
        """ Init Method """
        for attr in self.__slots__:
            if attr in options:
                setattr(self, attr, options[attr])
            else:
                setattr(self, attr, None)

    def __repr__(self):
        """ string representation """
        return 'GarminLap<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__)

    def read_lap_xml(self, ents):
        """ read lap from xml file """
        for ent in ents:
            if 'type' in ent:
                self.lap_type = ent.split('=')[1]
            elif 'index' in ent:
                self.lap_index = int(ent.split('=')[1])
            elif 'start' in ent:
                self.lap_start_string = ent.split('=')[1]
                self.lap_start = convert_date_string(self.lap_start_string)
            elif 'duration' in ent:
                tmp_ = ent.split('=')[1]
                self.lap_duration = float(convert_time_string(tmp_))
            elif 'distance' in ent:
                self.lap_distance = float(ent.split('=')[1])
            elif 'trigger' in ent:
                self.lap_trigger = ent.split('=')[1]
            elif 'max_speed' in ent:
                self.lap_max_speed = float(ent.split('=')[1])
            elif 'calories' in ent:
                self.lap_calories = int(ent.split('=')[1])
            elif 'avg_hr' in ent:
                self.lap_avg_hr = int(ent.split('=')[1])
            elif 'max_hr' in ent:
                self.lap_max_hr = int(ent.split('=')[1])
            elif 'intensity' in ent:
                self.lap_intensity = ent.split('=')[1]
            else:
                continue

    def read_lap_tcx(self, ents):
        """ read tcx lap entry """
        if len(ents) > 0:
            if 'StartTime' in ents[0]:
                self.lap_start_string = ents[0].split('=')[1]
                self.lap_start = convert_date_string(self.lap_start_string)
            elif 'TotalTimeSeconds' in ents[0]:
                self.lap_duration = float(ents[0].split('=')[1])
            elif 'DistanceMeters' in ents[0]:
                self.lap_distance = float(ents[0].split('=')[1])
            elif 'TriggerMethod' in ents[0]:
                self.lap_trigger = ents[0].split('=')[1]
            elif 'MaximumSpeed' in ents[0]:
                self.lap_max_speed = float(ents[0].split('=')[1])
            elif 'Calories' in ents[0]:
                self.lap_calories = int(ents[0].split('=')[1])
            elif 'AverageHeartRateBpm' in ents[0]:
                if 'Value' in ents[1]:
                    self.lap_avg_hr = int(ents[1].split('=')[1])
            elif 'MaximumHeartRateBpm' in ents[0]:
                if 'Value' in ents[1]:
                    self.lap_max_hr = int(ents[1].split('=')[1])
            elif 'Intensity' in ents[0]:
                self.lap_intensity = ents[0].split('=')[1]
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
        """ Init Method """
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
        """ string representation """
        return 'GarminFile<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__
                                            if x not in ['points', 'laps'])

    def calculate_speed(self):
        """
            calculate instantaneous speed (could maybe be a bit more elaborate)
        """
        for idx in range(1, len(self.points)):
            jdx = idx - 1
            t1_ = self.points[idx].time
            t0_ = self.points[jdx].time
            d1_ = self.points[idx].distance
            d0_ = self.points[jdx].distance
            if any([x == None for x in [t1_, t0_, d1_, d0_]]):
                continue
            totdur = (t1_ - t0_).total_seconds() # seconds
            totdis = d1_ - d0_ # meters
            if totdis > 0 and not self.points[idx].speed_permi:
                self.points[idx].speed_permi = (totdur/60.)\
                                                / (totdis/METERS_PER_MILE)
            if totdur > 0 and not self.points[idx].speed_mph:
                self.points[idx].speed_mph = (totdis/METERS_PER_MILE)\
                                              / (totdur/60./60.)
            if totdur > 0 and not self.points[idx].speed_mps:
                self.points[idx].speed_mps = totdis / totdur
            if d1_ > 0:
                self.points[idx].avg_speed_value_permi = \
                    ((t1_ - self.points[0].time).total_seconds()/60.)\
                     / (d1_/METERS_PER_MILE)
            if (t1_ - self.points[0].time).total_seconds() > 0:
                self.points[idx].avg_speed_value_mph = \
                    (self.points[idx].distance/METERS_PER_MILE)\
                     / ((t1_ - self.points[0].time).total_seconds()/60./60.)
