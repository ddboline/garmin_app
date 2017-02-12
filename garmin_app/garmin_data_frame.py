# -*- coding: utf-8 -*-
"""
    GarminDataFrame class
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)


class GarminDataFrame(object):
    """ dump list of garmin_points to pandas.DataFrame """

    def __init__(self, garmin_class=None, garmin_list=None):
        self.dataframe = None
        self.garminclass = garmin_class
        if garmin_class and garmin_list:
            self.fill_dataframe(garmin_list)

    def fill_dataframe(self, arr):
        """ fill dataframe """
        from pandas import DataFrame
        inp_array = []
        for it_ in arr:
            columns = []
            tmp_array = []
            for attr in self.garminclass._db_entries:
                columns.append(attr)
                tmp_array.append(getattr(it_, attr))
            inp_array.append(tmp_array)
        self.dataframe = DataFrame(inp_array, columns=columns)

    def fill_list(self):
        """ fill list """
        output = []
        for _, row in self.dataframe.iterrows():
            tmpobj = self.garminclass()
            for attr in self.garminclass._db_entries:
                setattr(tmpobj, attr, row[attr])
            output.append(tmpobj)
        return output
