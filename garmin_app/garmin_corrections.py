# -*- coding: utf-8 -*-
"""
    corrections for errors in original garmin files
    (by which I mean human errors)
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import json
from .garmin_utils import METERS_PER_MILE

FIVEK_DIST = 5000/METERS_PER_MILE

list_of_mislabeled_files = {'biking':
                                ['20101120T135534.gmn', '20110507T144308.gmn',
                                 '20110829T171218.gmn', '20111220T134356.gmn'],
                            'running':
                                ['20100816T175612.gmn', '20100825T165244.gmn',
                                 '20101031T145551.gmn', '20110524T171336.gmn',
                                 '20110627T161529.gmn', '20120504T172702.gmn'],
                            'walking':
                                ['20120428T112809.gmn', '20120519T103538.gmn',
                                 '20120519T104029.gmn', '20121231T154005.gmn'],
                            'stairs':
                                ['20120208T204305.gmn'],}

list_of_mislabeled_times = {'biking':
                                ['2010-11-20T14:55:34Z',
                                '2011-05-07T15:43:08Z',
                                '2011-08-29T18:12:18Z',
                                '2011-12-20T13:43:56Z',
                                '2011-08-06T13:59:30Z'],
                            'running':
                                ['2010-08-16T18:56:12Z',
                                '2010-08-25T17:52:44Z',
                                '2010-10-31T15:55:51Z',
                                '2011-01-02T16:23:19Z',
                                '2011-05-24T18:13:36Z',
                                '2011-06-27T17:15:29Z',
                                '2012-05-04T17:27:02Z',
                                '2014-02-09T14:26:59Z'],
                            'walking':
                                ['2012-04-28T11:28:09Z',
                                '2012-05-19T10:35:38Z',
                                '2012-05-19T10:40:29Z',
                                '2012-12-31T15:40:05Z'],
                            'stairs':
                                ['2012-02-08T20:43:05Z'],
                            'snowshoeing':
                                ['2013-12-25T19:34:06Z'],
                            'skiing':
                                ['2010-12-24T14:04:58Z',
                                '2013-12-26T21:24:38Z'],}

JSON_DIR = '%s/setup_files/build/garmin_app/garmin_app' % os.getenv('HOME')

_list_of_corrected_laps = {}

def list_of_corrected_laps(json_path=None):
    if not json_path:
        json_path = JSON_DIR
    if not os.path.exists(json_path):
        json_path = '%s/garmin_app/garmin_app' % os.getenv('HOME')
    if len(_list_of_corrected_laps) == 0:
        with open('%s/garmin_corrections.json' % json_path, 'r') as jfile_:
            tmp_dict = json.load(jfile_)
            for key, val in tmp_dict.items():
                tmp_ = {}
                for k2_, v2_ in val.items():
                    k2_ = int(k2_)
                    tmp_[k2_] = v2_
                _list_of_corrected_laps[key] = tmp_
    return _list_of_corrected_laps
        

def save_corrections(list_, json_path=None):
    """ save json file """
    if not json_path:
        json_path = JSON_DIR
    if not os.path.exists(json_path):
        os.makedirs(json_path)
    with open('%s/garmin_corrections.json' % json_path, 'w') as jfile:
        json.dump(list_, jfile, indent=1, sort_keys=True)

