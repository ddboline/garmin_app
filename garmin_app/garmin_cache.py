# -*- coding: utf-8 -*-

"""
    functions to read and write
    GarminFile, GarminSummary objects to and from pickle cache
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os

import gzip
from functools import partial
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

from garmin_app.util import walk_wrapper
from garmin_app.garmin_summary import GarminSummary
from garmin_app.garmin_utils import get_md5, print_date_string

try:
    import cPickle as pickle
except ImportError:
    import pickle

_work_list = []
NCPU = mp.cpu_count()
pool = ProcessPoolExecutor(max_workers=NCPU)


def read_pickle_object_in_file(pickle_file):
    """ read python object from gzipped pickle file """
    outobj = None
    if os.path.exists(pickle_file):
        try:
            with gzip.open(pickle_file, 'rb') as pkl_file:
                outobj = pickle.load(pkl_file)
        except UnicodeDecodeError:
            pass
    return outobj


def write_pickle_object_to_file(inpobj, pickle_file):
    """ write python object to gzipped pickle file """
    with gzip.open('%s.tmp' % pickle_file, 'wb') as pkl_file:
        pickle.dump(inpobj, pkl_file, pickle.HIGHEST_PROTOCOL)
    os.rename('%s.tmp' % pickle_file, pickle_file)
    return True


def _write_cached_file(garminfile, cache_directory):
    if not garminfile or not cache_directory:
        return False
    pkl_file = '%s/%s.pkl.gz' % (cache_directory, garminfile.filename)
    return write_pickle_object_to_file(garminfile, pkl_file)


def _read_file_in_par(init, cache_directory):
    reduced_gmn_filename, gmn_filename, gmn_md5sum, corr_list = init
    gsum = GarminSummary(gmn_filename, md5sum=gmn_md5sum, corr_list=corr_list)
    gfile = gsum.read_file()
    if gfile:
        _write_cached_file(gfile, cache_directory)
    outit = (reduced_gmn_filename, gmn_filename, gmn_md5sum, gsum)
    return outit


class GarminCache(object):
    """ class to manage caching objects """
    def __init__(self, pickle_file='', cache_directory='', corr_list=None,
                 cache_read_fn=read_pickle_object_in_file,
                 cache_write_fn=write_pickle_object_to_file, use_sql=True,
                 check_md5=False):
        self.pickle_file = pickle_file
        self.cache_directory = cache_directory
        self.cache_summary_list = []
        self.cache_summary_md5_dict = {}
        self.cache_summary_file_dict = {}
        self.cache_file_is_modified = False
        self.do_update = False
        self.check_md5 = check_md5
        if use_sql:
            from garmin_app.garmin_cache_sql import (read_postgresql_table,
                                                     write_postgresql_table)
            self.cache_read_fn = read_postgresql_table
            self.cache_write_fn = write_postgresql_table
        elif pickle_file:
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

    def read_cached_gfile(self, gfbname):
        """ return cached file """
        if not self.cache_directory:
            return False
        fname = '%s/%s.pkl.gz' % (self.cache_directory, gfbname)
        if not os.path.exists(fname):
            return False
        return read_pickle_object_in_file(fname)

    def write_cached_gfile(self, garminfile=None):
        """ write cached file """
        _write_cached_file(garminfile, self.cache_directory)

    def get_cache_summary_list(self, directory, options=None):
        """ return list of cached garmin_summary objects """
        self.do_update = False
        if options is None:
            options = {}
        if 'do_update' in options and options['do_update']:
            self.do_update = True
        summary_list = {}

        self.cache_file_is_modified = False
        temp_list = self.cache_read_fn()
        if temp_list:
            if isinstance(temp_list, dict):
                temp_list = list(temp_list.values())
            elif not isinstance(temp_list, list):
                temp_list = [temp_list]
            self.cache_summary_list = temp_list
        self.cache_summary_file_dict = {os.path.basename(x.filename):
                                        x for x in self.cache_summary_list}
        self.cache_summary_md5_dict = {x.md5sum:
                                       x for x in self.cache_summary_list
                                       if hasattr(x, 'md5sum')}

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
            _garmin_file_types = ('.gmn', '.tcx', '.fit', '.txt')
            if not any(a in gmn_filename.lower() for a in _garmin_file_types):
                return
            reduced_gmn_filename = os.path.basename(gmn_filename)
            local_dict = self.cache_summary_file_dict
            if self.check_md5 or reduced_gmn_filename not in local_dict:
                gmn_md5sum = get_md5(gmn_filename)
            else:
                gmn_md5sum = local_dict[reduced_gmn_filename].md5sum
            if ((reduced_gmn_filename not in local_dict) or
                    (hasattr(local_dict, 'md5sum') and
                     local_dict[reduced_gmn_filename].md5sum != gmn_md5sum) or
                    (self.do_update and print_date_string(
                     local_dict[reduced_gmn_filename].begin_datetime)
                        in self.corr_list)):
                self.cache_file_is_modified = True
                _job = pool.submit(_read_file_in_par,
                                   (reduced_gmn_filename, gmn_filename,
                                    gmn_md5sum, self.corr_list),
                                   self.cache_directory)
                _work_list.append((gmn_filename, _job))
            else:
                gsum = local_dict[reduced_gmn_filename]
                _res = (reduced_gmn_filename, gmn_filename, gmn_md5sum, gsum)
                _work_list.append((gmn_filename, _res))

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

        while len(_work_list) > 0:
            fn_, item = _work_list.pop(0)
            if hasattr(item, 'result'):
                try:
                    item = item.result()
                except AttributeError:
                    print(fn_)
                    raise
            reduced_gmn_filename, gmn_filename, gmn_md5sum, gsum = item
            self.cache_summary_file_dict[reduced_gmn_filename] = gsum
            self.cache_summary_md5_dict[gmn_md5sum] = gsum
            summary_list[gsum.filename] = gsum

        self.cache_summary_list = list(self.cache_summary_file_dict.values())

        if self.cache_file_is_modified:
            self.cache_write_fn(self.cache_summary_file_dict)
        return summary_list
