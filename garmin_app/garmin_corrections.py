# -*- coding: utf-8 -*-
"""
    corrections for errors in original garmin files
    (by which I mean human errors)
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import json
from garmin_app.garmin_utils import METERS_PER_MILE

FIVEK_DIST = 5000 / METERS_PER_MILE

DB_ENTRIES = ('id', 'start_time', 'lap_number', 'distance', 'duration')

LIST_OF_MISLABELED_TIMES = {
    'biking': [
        '2010-11-20T14:55:34Z', '2011-05-07T15:43:08Z', '2011-08-29T18:12:18Z',
        '2011-12-20T13:43:56Z', '2011-08-06T13:59:30Z', '2016-06-30T12:02:39Z'
    ],
    'running': [
        '2010-08-16T18:56:12Z', '2010-08-25T17:52:44Z', '2010-10-31T15:55:51Z',
        '2011-01-02T16:23:19Z', '2011-05-24T18:13:36Z', '2011-06-27T17:15:29Z',
        '2012-05-04T17:27:02Z', '2014-02-09T14:26:59Z'
    ],
    'walking': [
        '2012-04-28T11:28:09Z', '2012-05-19T10:35:38Z', '2012-05-19T10:40:29Z',
        '2012-12-31T15:40:05Z', '2017-04-29T10:04:04Z', '2017-07-01T09:47:14Z'
    ],
    'stairs': ['2012-02-08T20:43:05Z'],
    'snowshoeing': ['2013-12-25T19:34:06Z'],
    'skiing': ['2010-12-24T14:04:58Z', '2013-12-26T21:24:38Z', '2016-12-30T17:34:03Z']
}

JSON_DIR = '%s/setup_files/build/garmin_app/garmin_app' % os.getenv('HOME')

_LIST_OF_CORRECTED_LAPS = {}


def get_list_of_corrected_laps():
    return _LIST_OF_CORRECTED_LAPS


def list_of_corrected_laps(json_path=JSON_DIR, json_file='garmin_corrections.json'):
    """ return list_of_corrected_laps """
    if not os.path.exists(json_path):
        json_path = '%s/garmin_app/garmin_app' % os.getenv('HOME')
    if len(_LIST_OF_CORRECTED_LAPS) == 0:
        with open('%s/%s' % (json_path, json_file), 'rt') as jfile_:
            tmp_dict = json.load(jfile_)
            for key, val in tmp_dict.items():
                tmp_ = {}
                for k2_, v2_ in val.items():
                    k2_ = int(k2_)
                    tmp_[k2_] = v2_
                _LIST_OF_CORRECTED_LAPS[key] = tmp_
    return _LIST_OF_CORRECTED_LAPS


def save_corrections(list_, json_path=JSON_DIR, json_file='garmin_corrections.json'):
    """ save json file """
    if not os.path.exists(json_path):
        os.makedirs(json_path)
    with open('%s/%s' % (json_path, json_file), 'wt') as jfile:
        json.dump(list_, jfile, indent=1, sort_keys=True)
