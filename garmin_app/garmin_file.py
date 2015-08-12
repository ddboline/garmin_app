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

try:
    from itertools import izip
except ImportError:
    from builtins import zip as izip

from .garmin_utils import METERS_PER_MILE


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
        if len(self.points) > 0:
            self.points[0].avg_speed_value_permi = 0
            self.points[0].avg_speed_value_mph = 0
        for point0, point1 in izip(self.points[1:], self.points):
            t1_ = point0.time
            t0_ = point1.time
            d1_ = point0.distance
            d0_ = point1.distance
            if any([x == None for x in [t1_, t0_, d1_, d0_]]):
                continue
            totdur = (t1_ - t0_).total_seconds() # seconds
            totdis = d1_ - d0_ # meters
            if totdis > 0 and not point0.speed_permi:
                point0.speed_permi = (totdur/60.)\
                                                / (totdis/METERS_PER_MILE)
            if totdur > 0 and not point0.speed_mph:
                point0.speed_mph = (totdis/METERS_PER_MILE)\
                                              / (totdur/60./60.)
            if totdur > 0 and not point0.speed_mps:
                point0.speed_mps = totdis / totdur
            if d1_ > 0:
                point0.avg_speed_value_permi = \
                    ((t1_ - self.points[0].time).total_seconds()/60.)\
                     / (d1_/METERS_PER_MILE)
            if (t1_ - self.points[0].time).total_seconds() > 0:
                point0.avg_speed_value_mph = \
                    (point0.distance/METERS_PER_MILE)\
                     / ((t1_ - self.points[0].time).total_seconds()/60./60.)
