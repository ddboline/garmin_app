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

from garmin_app.garmin_file import GarminSummary, GarminFile, GarminLap, GarminPoint
from garmin_app.garmin_utils import get_md5_full

class GarminCache(object):
    ''' class to manage caching objects '''
    def __init__(self, pickle_file=''):
        self.pickle_file = pickle_file
        self.summary_list = []
        self.summary_md5_dict = {}
        self.summary_file_dict = {}
        self.pickle_file_is_modified = False
        pass
    
    def read_pickle_object_in_file(self):
        ''' read python object from gzipped pickle file '''
        if not self.pickle_file:
            return None
        outobj = None
        if os.path.exists(self.pickle_file):
            with gzip.open(self.pickle_file, 'rb') as pkl_file:
                outobj = pickle.load(pkl_file)
        return outobj
        
    def write_pickle_object_to_file(self, inpobj):
        ''' write python object to gzipped pickle file '''
        if not self.pickle_file:
            return False
        with gzip.open('%s.tmp' % self.pickle_file, 'wb') as pkl_file:
            pickle.dump(inpobj, pkl_file, pickle.HIGHEST_PROTOCOL)
        run_command('mv %s.tmp %s' % (self.pickle_file, self.pickle_file))
        return True

    def get_summary_list(self, directory, **options):
        ''' '''
        #opts = ['do_plot', 'do_year', 'do_month', 'do_week', 'do_day', 'do_file', 'do_sport', 'do_update', 'do_average']
        #do_plot, do_year, do_month, do_week, do_day, do_file, do_sport, do_update, do_average = [options[o] for o in opts]
        self.pickle_file_is_modified = False
        temp_list = self.read_pickle_object_in_file()
        if temp_list and type(temp_list) == list:
            self.summary_list = temp_list
        self.summary_file_dict = {os.path.basename(x.filename): x for x in self.summary_list}
        self.summary_md5_dict = {x.md5sum: x for x in self.summary_list}

        def process_files(arg, dirname, names):
            for name in names:
                gmn_filename = '%s/%s' % (dirname, name)
                if os.path.isdir(gmn_filename):
                    continue
                if '.pkl' in gmn_filename:
                    continue
                add_file(gmn_filename)

        def add_file(gmn_filename):
            if not any(a in gmn_filename.lower() for a in ['.gmn', '.tcx', '.fit', '.txt']):
                return
            reduced_gmn_filename = os.path.basename(gmn_filename)
            gmn_md5sum = get_md5_full(gmn_filename)

            if ((reduced_gmn_filename not in self.summary_file_dict) or
                    (self.summary_file_dict[reduced_gmn_filename].md5sum != gmn_md5sum) or
                    (do_update and print_date_string(self.summary_md5_dict[reduced_gmn_filename].begin_time)
                        in list_of_corrected_laps)):
                self.pickle_file_is_modified = True
                gfile = GarminSummary(gmn_filename, md5sum=gmn_md5sum)
                if gfile.read_file():
                    self.summary_md5_dict[reduced_gmn_filename] = gfile
                else:
                    print 'file %s not loaded for some reason' % reduced_gmn_filename
            else:
                gfile = self.summary_file_dict[reduced_gmn_filename]
            self.summary_list.append(gfile)
            self.summary_file_dict[reduced_gmn_filename] = gfile
            self.summary_md5_dict[gmn_md5sum] = gfile
        
        if type(directory) == str:
            if os.path.isdir(directory):
                os.path.walk(directory, process_files, None)
            elif os.path.isfile(directory):
                add_file(directory)
        if type(directory) == list:
            for d in directory:
                if os.path.isdir(d):
                    os.path.walk(d, process_files, None)
                elif os.path.isfile(d):
                    add_file(d)

        if self.pickle_file_is_modified:
            if not self.write_pickle_object_to_file(self.summary_list):
                print 'ERROR: failed to write pickle file'
                return False
            else:
                return self.summary_list
        


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

