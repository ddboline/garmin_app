#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    module holds GarminSummary class
'''

import os

from garmin_app.garmin_utils import get_md5, expected_calories,\
                                    SPORT_TYPES, METERS_PER_MILE

class GarminSummary(object):
    ''' summary class for a file '''
    __slots__ = ['filename', 'begin_datetime', 'sport',
                 'total_calories', 'total_distance', 'total_duration',
                 'total_hr_dur', 'total_hr_dis', 'number_of_items',
                 'md5sum']

    def __init__(self, filename='', md5sum=None):
        self.filename = filename
        self.begin_datetime = None
        self.sport = None
        self.total_calories = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_hr_dur = 0
        self.total_hr_dis = 0
        self.number_of_items = 0
        if md5sum:
            self.md5sum = md5sum
        elif self.filename != '':
            self.md5sum = get_md5(self.filename)

    def __repr__(self):
        return 'GarminSummary<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in self.__slots__)

    def read_file(self):
        '''  read the file, calculate some stuff '''
        from garmin_app.garmin_parse import GarminParse
        temp_gfile = GarminParse(self.filename)
        temp_gfile.read_file()
        self.begin_datetime = temp_gfile.begin_datetime
        self.sport = temp_gfile.sport
        self.total_calories = temp_gfile.total_calories
        self.total_distance = temp_gfile.total_distance
        self.total_duration = temp_gfile.total_duration
        self.total_hr_dur = temp_gfile.total_hr_dur
        self.total_hr_dis = temp_gfile.total_hr_dis
        self.number_of_items += 1

        if self.total_calories == 0 and self.sport == 'running' and self.total_distance > 0.0:
            self.total_calories = int(expected_calories(weight=175, pace_min_per_mile=(self.total_duration / 60.) / (self.total_distance / METERS_PER_MILE), distance=self.total_distance / METERS_PER_MILE))
        elif self.total_calories == 0 and self.sport == 'stairs' and self.total_duration > 0:
            self.total_calories = 325 * (self.total_duration / 1100.89)
        elif self.total_calories == 0:
            return temp_gfile
        if self.total_calories < 3:
            return temp_gfile
        if self.sport not in SPORT_TYPES:
            print '%s not supported' % self.sport
            return False

        return temp_gfile


    def add(self, summary_to_add):
        ''' add to totals '''
        self.total_calories += summary_to_add.total_calories
        self.total_distance += summary_to_add.total_distance
        self.total_duration += summary_to_add.total_duration
        if summary_to_add.total_hr_dur > 0:
            self.total_hr_dur += summary_to_add.total_hr_dur
            self.total_hr_dis += summary_to_add.total_hr_dis
        self.number_of_items += 1