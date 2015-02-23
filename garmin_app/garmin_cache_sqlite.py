#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    functions to read and write
    GarminFile, GarminSummary objects to and from cache
    
    desired caches:
        python pickle
        SQL
        amazon S3
'''


class GarminCache(object):
    ''' class to manage caching objects '''
    def __init__(self, sqlite_file='', cache_directory=''):
        self.sqlite_file = sqlite_file
        self.cache_directory = cache_directory
        self.cache_summary_list = []
        self.cache_summary_md5_dict = {}
        self.cache_summary_file_dict = {}
        self.sqlite_file_is_modified = False
        self.do_update = False
        if cache_directory:
            if not os.path.exists(cache_directory):
                os.makedirs(cache_directory)

    def read_sqlite_object_in_file(self, sqlite_file=''):
        ''' read python object from sqlite file '''
        return
        
    def write_pickle_object_to_file(self, inpobj, sqlite_file=''):
        ''' write python object to gzipped pickle file '''
        return True

    def read_cached_gfile(self, gfbasename=''):
        return
        
    def write_cached_gfile(self, garminfile=None):
        return

    def get_cache_summary_list(self, directory, **options):
        ''' '''
        self.do_update = False
        if 'update' in options and options['update']:
            self.do_update = True
        summary_list = []
        
        self.sqlite_file_is_modified = False
        temp_list = self.read_pickle_object_in_file()
        if temp_list and type(temp_list) == list:
            self.cache_summary_list = temp_list
        self.cache_summary_file_dict = {os.path.basename(x.filename): x for x in self.cache_summary_list}
        self.cache_summary_md5_dict = {x.md5sum: x for x in self.cache_summary_list}

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
            gmn_md5sum = get_md5(gmn_filename)

            if ((reduced_gmn_filename not in self.cache_summary_file_dict) or
                    (self.cache_summary_file_dict[reduced_gmn_filename].md5sum != gmn_md5sum) or
                    (self.do_update and print_date_string(self.cache_summary_md5_dict[reduced_gmn_filename].begin_time)
                        in list_of_corrected_laps)):
                self.sqlite_file_is_modified = True
                gsum = GarminSummary(gmn_filename, md5sum=gmn_md5sum)
                gfile = gsum.read_file()
                if gfile:
                    self.cache_summary_list.append(gsum)
                    self.cache_summary_file_dict[reduced_gmn_filename] = gsum
                    self.cache_summary_md5_dict[gmn_md5sum] = gsum
                    self.write_cached_gfile(garminfile=gfile)
                else:
                    print 'file %s not loaded for some reason' % reduced_gmn_filename
            else:
                gsum = self.cache_summary_file_dict[reduced_gmn_filename]
            summary_list.append(gsum)
        
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

        if self.sqlite_file_is_modified:
            self.write_pickle_object_to_file(self.cache_summary_list)
        return summary_list
