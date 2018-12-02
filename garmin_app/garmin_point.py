# -*- coding: utf-8 -*-
"""
    GarminPoint Class
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

from dateutil.parser import parse

from garmin_app.garmin_utils import convert_date_string, METERS_PER_MILE


class GarminPoint(object):
    """
        point representing each gps point
    """
    _db_entries = [
        'time', 'latitude', 'longitude', 'altitude', 'distance', 'heart_rate', 'duration_from_last',
        'duration_from_begin', 'speed_mps', 'speed_permi', 'speed_mph', 'avg_speed_value_permi',
        'avg_speed_value_mph'
    ]
    __slots__ = _db_entries

    _avro_schema = {
        'namespace':
        'garmin.avro',
        'type':
        'record',
        'name':
        'GarminPoint',
        'fields': [
            {
                'name': 'time',
                'type': 'string'
            },
            {
                'name': 'latitude',
                'type': ['double', 'null']
            },
            {
                'name': 'longitude',
                'type': ['double', 'null']
            },
            {
                'name': 'altitude',
                'type': ['double', 'null']
            },
            {
                'name': 'distance',
                'type': ['double', 'null']
            },
            {
                'name': 'heart_rate',
                'type': ['double', 'null']
            },
            {
                'name': 'duration_from_last',
                'type': 'double'
            },
            {
                'name': 'duration_from_begin',
                'type': 'double'
            },
            {
                'name': 'speed_mps',
                'type': 'double'
            },
            {
                'name': 'speed_permi',
                'type': 'double'
            },
            {
                'name': 'speed_mph',
                'type': 'double'
            },
            {
                'name': 'avg_speed_value_permi',
                'type': 'double'
            },
            {
                'name': 'avg_speed_value_mph',
                'type': 'double'
            },
        ]
    }

    def __init__(self, **options):
        """ Init Method """
        for attr in self.__slots__:
            if attr in options:
                setattr(self, attr, options[attr])
            else:
                setattr(self, attr, None)
        self.duration_from_last = 0.  # keep a running total for convenience
        self.duration_from_begin = 0.  # keep a running total for convenience
        self.speed_mps = 0.
        self.speed_permi = -1.
        self.speed_mph = 0.
        self.avg_speed_value_permi = -1.
        self.avg_speed_value_mph = 0.

    def __repr__(self):
        """ string representation """
        return 'GarminPoint<%s>' % ', '.join('%s=%s' % (x, getattr(self, x))
                                             for x in self.__slots__)

    def __eq__(self, other):
        for field in self.__slots__:
            value0 = getattr(self, field)
            value1 = getattr(other, field)
            if isinstance(value0, float) and isinstance(value1, float):
                if abs(value0 - value1) > 0.01:
                    return False
            else:
                if value0 != value1:
                    return False
        return True

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
                        self.speed_mph = (self.speed_mps * 3600. / METERS_PER_MILE)
                        if self.speed_mps > 0.:
                            self.speed_permi = (METERS_PER_MILE / self.speed_mps / 60.)

    def to_dict(self):
        output = {}
        for field in self._avro_schema['fields']:
            name = field['name']
            type_ = field['type']
            if 'time' in name:
                output[name] = getattr(self, name).isoformat()
            elif type_ == 'int':
                output[name] = int(getattr(self, name))
            else:
                output[name] = getattr(self, name)
        return output

    @staticmethod
    def from_dict(record):
        gpoint = GarminPoint()
        for field in GarminPoint._avro_schema['fields']:
            name = field['name']
            if 'time' in name:
                setattr(gpoint, name, parse(record[name]))
            else:
                setattr(gpoint, name, record[name])
        return gpoint
