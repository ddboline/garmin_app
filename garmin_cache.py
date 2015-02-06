#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    module will hold functions to read and write
    GarminFile, GarminSummary objects to and from cache
    
    desired caches:
        python pickle
        SQL
        amazon S3
        
'''

import os
import gzip

try:
    import cPickle as pickle
except ImportError:
    import pickle

import pandas as pd

try:
    from util import run_command
except ImportError:
    if os.path.exists('%s/scripts' % os.getenv('HOME')):
        os.sys.path.append('%s/scripts' % os.getenv('HOME'))
        from util import run_command

from garmin_file import GarminSummary, GarminFile, GarminLap, GarminPoint

class GarminCache(object):
    ''' class to manage caching objects '''
    def __init__(self, pickle_file=''):
        self.pickle_file = pickle_file
        pass
    
    def read_pickle_object_in_file(self):
        if not self.pickle_file:
            return None
        outobj = None
        if os.path.exists(self.pickle_file):
            with gzip.open(self.pickle_file, 'rb') as pkl_file:
                outobj = pickle.load(pkl_file)
        return outobj
        
    def write_pickle_object_to_file(self, inpobj):
        if not self.pickle_file:
            return False
        with gzip.open('%s.tmp' % self.pickle_file, 'wb') as pkl_file:
            pickle.dump(inpobj, pkl_file, pickle.HIGHEST_PROTOCOL)
        run_command('mv %s.tmp %s' % (self.pickle_file, self.pickle_file))
        return True

class GarminDataFrame(object):
    ''' dump list of garmin_points to pandas.DataFrame '''
    def __init__(self, garmin_class=None, garmin_list=None):
        self.dataframe = None
        if garmin_class and garmin_list:
            self.fill_dataframe(garmin_class.__slots__, garmin_list)

    def fill_dataframe(self, attrs, arr):
        inp_array = []
        for it in arr:
            tmp_array = []
            for attr in attrs:
                tmp_array.append(getattr(it, attr))
            inp_array.append(tmp_array)
        self.dataframe = pd.DataFrame(inp_array, columns=attrs)

