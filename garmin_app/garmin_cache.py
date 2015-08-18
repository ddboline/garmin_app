# -*- coding: utf-8 -*-

"""
    functions to read and write
    GarminFile, GarminSummary objects to and from pickle cache
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import gzip
from functools import partial

from .util import run_command, walk_wrapper
from .garmin_summary import GarminSummary
from .garmin_utils import get_md5, print_date_string

try:
    import cPickle as pickle
except ImportError:
    import pickle

def read_pickle_object_in_file(pickle_file):
    """ read python object from gzipped pickle file """
    outobj = None
    if os.path.exists(pickle_file):
        with gzip.open(pickle_file, 'rb') as pkl_file:
            try:
                outobj = pickle.load(pkl_file)
            except UnicodeDecodeError:
                print('failed to load from pickle, continuing')
                return None
    return outobj

def write_pickle_object_to_file(inpobj, pickle_file):
    """ write python object to gzipped pickle file """
    with gzip.open('%s.tmp' % pickle_file, 'wb') as pkl_file:
        pickle.dump(inpobj, pkl_file, pickle.HIGHEST_PROTOCOL)
    run_command('mv %s.tmp %s' % (pickle_file, pickle_file))
    return True


class GarminCache(object):
    """ class to manage caching objects """
    def __init__(self, pickle_file='', cache_directory='', corr_list=None,
                 cache_read_fn=read_pickle_object_in_file,
                 cache_write_fn=write_pickle_object_to_file):
        self.pickle_file = pickle_file
        self.cache_directory = cache_directory
        self.cache_summary_list = []
        self.cache_summary_md5_dict = {}
        self.cache_summary_file_dict = {}
        self.cache_file_is_modified = False
        self.do_update = False
        if pickle_file:
            self.cache_read_fn = partial(cache_read_fn,
                                         pickle_file=self.pickle_file)
            self.cache_write_fn = partial(cache_write_fn,
                                          pickle_file=self.pickle_file)
        else:
            self.cache_read_fn = cache_read_fn
            self.cache_write_fn = cache_write_fn
        if cache_directory:
            if not os.path.exists(cache_directory):
                os.makedirs(cache_directory)
        self.corr_list = []
        if corr_list:
            self.corr_list = corr_list

    def read_cached_gfile(self, gfbasename=''):
        """ return cached file """
        if not gfbasename or not self.cache_directory:
            return False
        fname = '%s/%s.pkl.gz' % (self.cache_directory, gfbasename)
        if not os.path.exists(fname):
            return False
        else:
            return read_pickle_object_in_file(fname)

    def write_cached_gfile(self, garminfile=None):
        """ write cached file """
        if not garminfile or not self.cache_directory:
            return False
        gfbasename = os.path.basename(garminfile.orig_filename)
        pkl_file = '%s/%s.pkl.gz' % (self.cache_directory, gfbasename)
        return write_pickle_object_to_file(garminfile, pkl_file)

    def get_cache_summary_list(self, directory, options=None):
        """ return list of cached garmin_summary objects """
        self.do_update = False
        if options is None:
            options = {}
        if 'do_update' in options and options['do_update']:
            self.do_update = True
        summary_list = []

        self.cache_file_is_modified = False
        temp_list = self.cache_read_fn()
        if temp_list and type(temp_list) == list:
            self.cache_summary_list = temp_list
        self.cache_summary_file_dict = {os.path.basename(x.filename):
                                        x for x in self.cache_summary_list}
        self.cache_summary_md5_dict = {x.md5sum:
                                       x for x in self.cache_summary_list}

        def process_files(_, dirname, names):
            """ callback function for os.walk """
            for name in names:
                gmn_filename = '%s/%s' % (dirname, name)
                if os.path.isdir(gmn_filename):
                    continue
                if '.pkl' in gmn_filename:
                    continue
                add_file(gmn_filename)

        def add_file(gmn_filename):
            """ generate garmin_summary """
            if not any(a in gmn_filename.lower() for a in ['.gmn', '.tcx',
                                                           '.fit', '.txt']):
                return
            reduced_gmn_filename = os.path.basename(gmn_filename)
            gmn_md5sum = get_md5(gmn_filename)
            if ((reduced_gmn_filename not in self.cache_summary_file_dict) or
                    (self.cache_summary_file_dict[reduced_gmn_filename].md5sum
                     != gmn_md5sum) or
                    (self.do_update
                     and print_date_string(
                         self.cache_summary_file_dict[reduced_gmn_filename]\
                             .begin_datetime)
                        in self.corr_list)):
                self.cache_file_is_modified = True
                gsum = GarminSummary(gmn_filename, md5sum=gmn_md5sum,
                                     corr_list=self.corr_list)
                gfile = gsum.read_file()
                if gfile:
                    self.cache_summary_file_dict[reduced_gmn_filename] = gsum
                    self.cache_summary_md5_dict[gmn_md5sum] = gsum
                    self.write_cached_gfile(garminfile=gfile)
                else:
                    print('file %s not loaded for some reason'
                          % reduced_gmn_filename)
            else:
                gsum = self.cache_summary_file_dict[reduced_gmn_filename]
            summary_list.append(gsum)


        if type(directory) == list:
            for dr_ in directory:
                if os.path.isdir(dr_):
                    walk_wrapper(dr_, process_files, None)
                elif os.path.isfile(dr_):
                    add_file(dr_)
        elif directory:
            if os.path.isdir(directory):
                walk_wrapper(directory, process_files, None)
            elif os.path.isfile(directory):
                add_file(directory)

        self.cache_summary_list = list(self.cache_summary_file_dict.values())

        if self.cache_file_is_modified:
            self.cache_write_fn(self.cache_summary_list)
        return summary_list
