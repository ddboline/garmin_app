# -*- coding: utf-8 -*-
"""
    GarminLap Class
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .garmin_utils import (convert_date_string, convert_time_string)


class GarminLap(object):
    """
        class representing each lap in xml file
            functions:
                read_lap_xml(node), read_lap_tcx(node), print_lap_string(node)
    """
    _db_entries = ['lap_type', 'lap_index', 'lap_start', 'lap_duration',
                   'lap_distance', 'lap_trigger', 'lap_max_speed',
                   'lap_calories', 'lap_avg_hr', 'lap_max_hr', 'lap_intensity',
                   'lap_number', 'lap_start_string']
    __slots__ = _db_entries

    def __init__(self, **options):
        """ Init Method """
        self.lap_type = None
        self.lap_index = None
        self.lap_start = None
        self.lap_duration = None
        self.lap_distance = None
        self.lap_trigger = None
        self.lap_max_speed = None
        self.lap_calories = None
        self.lap_avg_hr = None
        self.lap_max_hr = None
        self.lap_intensity = None
        self.lap_number = None
        self.lap_start_string = None
        for attr in self._db_entries:
            if attr in options:
                setattr(self, attr, options[attr])
            else:
                setattr(self, attr, None)

    def __repr__(self):
        """ string representation """
        return 'GarminLap<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self._db_entries)

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
