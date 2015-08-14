# -*- coding: utf-8 -*-
"""
    GarminPoint Class
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .garmin_utils import convert_date_string, METERS_PER_MILE


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
        self.duration_from_last = 0. ### keep a running total for convenience
        self.duration_from_begin = 0. ### keep a running total for convenience
        self.speed_mps = 0.
        self.speed_permi = -1.
        self.speed_mph = 0.
        self.avg_speed_value_permi = -1.
        self.avg_speed_value_mph = 0.

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
