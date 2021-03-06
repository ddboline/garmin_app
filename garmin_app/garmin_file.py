# -*- coding: utf-8 -*-
"""
    module holds GarminFile class
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
from dateutil.parser import parse
try:
    from itertools import izip
except ImportError:
    from builtins import zip as izip

from garmin_app.garmin_lap import GarminLap
from garmin_app.garmin_point import GarminPoint
from garmin_app.garmin_utils import METERS_PER_MILE


class GarminFile(object):
    """
        class representing a full xml file
            functions:
                read_file(), read_file_tcx(), read_file_xml(),
                print_file_string(), calculate_speed(), print_splits()
    """
    _db_entries = [
        'filename', 'filetype', 'begin_datetime', 'sport', 'total_calories', 'total_distance',
        'total_duration', 'total_hr_dur', 'total_hr_dis'
    ]
    __slots__ = _db_entries + ['orig_filename', 'laps', 'points']
    garmin_file_types = ('txt', 'tcx', 'fit', 'gpx', 'gmn')

    _avro_schema = {
        'namespace':
        'garmin.avro',
        'type':
        'record',
        'name':
        'GarminFile',
        'fields': [
            {
                'name': 'filename',
                'type': 'string'
            },
            {
                'name': 'filetype',
                'type': 'string'
            },
            {
                'name': 'begin_datetime',
                'type': 'string'
            },
            {
                'name': 'sport',
                'type': ['string', 'null']
            },
            {
                'name': 'total_calories',
                'type': 'int'
            },
            {
                'name': 'total_distance',
                'type': 'double'
            },
            {
                'name': 'total_duration',
                'type': 'double'
            },
            {
                'name': 'total_hr_dur',
                'type': 'double'
            },
            {
                'name': 'total_hr_dis',
                'type': 'double'
            },
            {
                'name': 'laps',
                'type': {
                    'type': 'array',
                    'items': GarminLap._avro_schema
                }
            },
            {
                'name': 'points',
                'type': {
                    'type': 'array',
                    'items': GarminPoint._avro_schema
                }
            },
        ]
    }

    def __init__(self, filename='', filetype=''):
        """ Init Method """
        if filename != '':
            self.orig_filename = filename
            self.filename = os.path.basename(filename)
            if not os.path.exists(filename):
                raise IOError
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
        return 'GarminFile<%s>' % ', '.join('%s=%s' % (x, getattr(self, x))
                                            for x in self._db_entries)

    def __eq__(self, other):
        for field in self._db_entries:
            value0 = getattr(self, field)
            value1 = getattr(other, field)
            if isinstance(value0, float) and isinstance(value1, float):
                if abs(value0 - value1) > 0.01:
                    return False
            else:
                if value0 != value1:
                    return False
        for field in 'laps', 'points':
            for l0, l1 in zip(getattr(self, field), getattr(other, field)):
                if l0 != l1:
                    return False
        return True

    def calculate_speed(self):
        """
            calculate instantaneous speed (could maybe be a bit more elaborate)
        """
        if len(self.points) > 0:
            self.points[0].avg_speed_value_permi = 0.
            self.points[0].avg_speed_value_mph = 0.
        for point0, point1 in izip(self.points[1:], self.points):
            t1_ = point0.time
            t0_ = point1.time
            d1_ = point0.distance
            d0_ = point1.distance
            if any([x is None for x in [t1_, t0_, d1_, d0_]]):
                continue
            totdur = (t1_ - t0_).total_seconds()  # seconds
            totdis = d1_ - d0_  # meters
            if totdis > 0 and not point0.speed_permi:
                point0.speed_permi = (totdur / 60.) / (totdis / METERS_PER_MILE)
            if totdur > 0 and not point0.speed_mph:
                point0.speed_mph = (totdis / METERS_PER_MILE) / (totdur / 3600.)
            if totdur > 0 and not point0.speed_mps:
                point0.speed_mps = totdis / totdur
            if d1_ > 0:
                point0.avg_speed_value_permi = ((
                    (t1_ - self.points[0].time).total_seconds() / 60.) / (d1_ / METERS_PER_MILE))
            if (t1_ - self.points[0].time).total_seconds() > 0:
                point0.avg_speed_value_mph = ((point0.distance / METERS_PER_MILE) / (
                    (t1_ - self.points[0].time).total_seconds() / 3600.))

    def to_dict(self):
        output = {}
        for field in self._avro_schema['fields']:
            name = field['name']
            type_ = field['type']
            if 'time' in name:
                output[name] = getattr(self, name).isoformat()
            elif type_ == 'array':
                continue
            elif type_ == 'int':
                output[name] = int(getattr(self, name))
            else:
                output[name] = getattr(self, name)
        output['laps'] = [lap.to_dict() for lap in self.laps]
        output['points'] = [point.to_dict() for point in self.points]
        return output

    @staticmethod
    def from_dict(record):
        gfile = GarminFile()
        for field in GarminFile._avro_schema['fields']:
            name = field['name']
            type_ = field['type']
            if 'time' in name:
                setattr(gfile, name, parse(record[name]))
            elif type_ == 'array':
                continue
            else:
                setattr(gfile, name, record[name])
        setattr(gfile, 'laps', [GarminLap.from_dict(lap) for lap in record['laps']])
        setattr(gfile, 'points', [GarminPoint.from_dict(point) for point in record['points']])

        return gfile
