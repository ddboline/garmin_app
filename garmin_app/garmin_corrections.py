#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    corrections for errors in original garmin files (by which I mean human errors)
'''
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from garmin_app.garmin_utils import METERS_PER_MILE, MARATHON_DISTANCE_MI

FIVEK_DIST = 5000/METERS_PER_MILE

list_of_mislabeled_files = {'biking':
                                ['20101120T135534.gmn', '20110507T144308.gmn', '20110829T171218.gmn', '20111220T134356.gmn'],
                            'running':
                                ['20100816T175612.gmn', '20100825T165244.gmn', '20101031T145551.gmn', '20110524T171336.gmn', '20110627T161529.gmn', '20120504T172702.gmn'],
                            'walking':
                                ['20120428T112809.gmn', '20120519T103538.gmn', '20120519T104029.gmn', '20121231T154005.gmn'],
                            'stairs':
                                ['20120208T204305.gmn'],}

list_of_mislabeled_times = {'biking':
                                ['2010-11-20T14:55:34Z', '2011-05-07T15:43:08Z', '2011-08-29T18:12:18Z', '2011-12-20T13:43:56Z', '2011-08-06T13:59:30Z'],
                            'running':
                                ['2010-08-16T18:56:12Z', '2010-08-25T17:52:44Z', '2010-10-31T15:55:51Z', '2011-01-02T16:23:19Z', '2011-05-24T18:13:36Z', '2011-06-27T17:15:29Z', '2012-05-04T17:27:02Z', '2014-02-09T14:26:59Z'],
                            'walking':
                                ['2012-04-28T11:28:09Z', '2012-05-19T10:35:38Z', '2012-05-19T10:40:29Z', '2012-12-31T15:40:05Z'],
                            'stairs':
                                ['2012-02-08T20:43:05Z'],
                            'snowshoeing':
                                ['2013-12-25T19:34:06Z'],
                            'skiing':
                                ['2010-12-24T14:04:58Z', '2013-12-26T21:24:38Z'],}

list_of_corrected_laps = {
     '2011-07-04T08:58:27Z': {0: FIVEK_DIST,},
     '2012-03-13T18:21:11Z': {0: 0.362,},
     '2012-03-13T18:25:14Z': {0: 0.556, 1: 0.294,},
     '2012-11-26T17:27:21Z': {0: 0.5,},
     '2012-11-28T17:27:42Z': {0: 0.5,},
     '2012-12-03T17:27:35Z': {0: 0.5,},
     '2012-12-04T17:36:49Z': {0: 0.300000,},
     '2012-12-05T17:27:10Z': {0: 0.500000,},
     '2012-12-06T16:06:01Z': {0: 0.300000,},
     '2012-12-11T15:05:05Z': {0: 0.446061,},
     '2012-12-18T15:09:20Z': {0: 0.500000,},
     '2012-12-19T16:12:19Z': {0: 0.700000,},
     '2012-12-20T16:19:24Z': {0: 0.500000,},
     '2013-01-07T15:33:33Z': {0: 0.473568,},
     '2013-01-08T16:24:07Z': {0: 0.500000,},
     '2013-01-15T14:59:01Z': {0: 0.500000,},
     '2013-01-17T16:14:32Z': {0: 0.507143, 1: 0.190476,},
     '2013-01-24T15:12:22Z': {0: 0.310000,},
     '2013-01-25T16:10:48Z': {0: 0.500000,},
     '2013-01-28T17:23:39Z': {0: 0.599443,},
     '2013-01-29T17:12:57Z': {0: 0.749312,},
     '2013-01-30T17:24:01Z': {0: 0.498701,},
     '2013-02-01T17:23:27Z': {0: 0.598760,},
     '2013-02-04T17:25:21Z': {0: 0.599403,},
     '2013-02-05T17:46:03Z': {0: 5.489645,},
     '2013-02-06T17:17:07Z': {0: 0.629378,},
     '2013-02-12T17:43:11Z': {0: 0.798967,},
     '2013-02-13T17:23:52Z': {0: 0.799703,},
     '2013-02-20T17:24:13Z': {0: 0.498111,},
     '2013-02-22T17:06:24Z': {0: 0.399090, 1: 0.139218, 2: 0.181911,},
     '2013-02-25T17:25:30Z': {0: 0.400000,},
     '2013-02-27T17:24:38Z': {0: 0.498379,},
     '2013-03-18T17:25:15Z': {0: 0.499211,},
     '2013-03-20T17:31:22Z': {0: 0.499816,},
     '2013-03-21T17:30:03Z': {0: 0.679391,},
     '2013-03-22T17:26:21Z': {0: 0.498697,},
     '2013-03-27T17:25:50Z': {0: 0.498794,},
     '2013-03-29T17:24:25Z': {0: 0.498196,},
     '2013-04-01T17:25:56Z': {0: 0.498132,},
     '2013-04-08T17:25:17Z': {0: 0.497942,},
     '2013-04-09T17:35:15Z': {0: 0.699718,},
     '2013-04-10T17:26:08Z': {0: 0.498825,},
     '2013-04-15T17:24:51Z': {0: 0.499177,},
     '2013-04-16T17:40:49Z': {0: 0.998147,},
     '2013-04-17T17:25:55Z': {0: 0.500000,},
     '2013-04-19T17:25:54Z': {0: 0.498889,},
     '2013-04-22T17:25:17Z': {0: 0.498933,},
     '2013-04-23T17:24:28Z': {0: 0.699618,},
     '2013-04-24T17:26:35Z': {0: 0.498244,},
     '2013-04-26T17:25:33Z': {0: 0.499962,},
     '2013-04-29T17:25:42Z': {0: 0.499923,},
     '2013-05-01T17:23:36Z': {0: 0.799678,},
     '2013-05-03T17:24:44Z': {0: 0.499960,},
     '2013-05-06T17:27:24Z': {0: 0.498519,},
     '2013-05-14T17:39:00Z': {0: 0.299113,},
     '2013-05-15T17:26:25Z': {0: 0.499869,},
     '2013-05-21T16:49:49Z': {0: 0.799861,},
     '2013-08-08T06:24:20Z': {0: 0.498713,},
     '2013-08-21T17:56:26Z': {0: 0.898884,},
     '2013-08-26T17:29:25Z': {0: 0.627997,},
     '2013-08-27T14:56:32Z': {0: 0.500000,},
     '2013-09-09T17:27:21Z': {0: 0.600000,},
     '2013-09-10T17:35:40Z': {0: 0.639421,},
     '2013-09-19T16:59:06Z': {0: 0.639288,},
     '2013-10-03T06:34:03Z': {0: 5.498913,},
     '2013-10-07T06:35:22Z': {0: 5.499870,},
     '2013-10-09T06:33:07Z': {0: 5.499864,},
     '2013-10-10T06:59:58Z': {0: 6.498988,},
     '2013-10-11T07:05:25Z': {0: 2.998719,},
     '2013-10-13T07:00:47Z': {0: 10.36,},
     '2013-10-14T06:36:14Z': {0: 4.748939,},
     '2013-10-15T07:03:55Z': {0: 3.499039,},
     '2013-10-23T15:58:39Z': {0: 0.499755,},
     '2013-10-24T15:56:25Z': {0: 0.498953,},
     '2013-11-01T11:03:05Z': {0: 5.8,},
     '2013-12-05T12:15:14Z': {0: 4.8,},
     '2013-12-16T19:59:43Z': {0: 0.45,},
     '2013-12-18T20:25:11Z': {0: 4.8,},
     '2013-12-20T20:26:08Z': {0: 5.8,},
     '2014-01-09T19:32:40Z': {0: 8.3,},
     '2014-01-15T20:17:37Z': {0: 4.0,},
     '2014-01-20T14:34:40Z': {0: 4.5,},
     '2014-01-21T12:28:44Z': {0: 6.7,},
     '2014-01-25T12:49:08Z': {5: [2.75, 25.29*60]},
     '2014-01-30T21:07:26Z': {0: 0.34,},
     '2014-02-01T12:06:19Z': {0: [9.41, 78.82*60],},
     '2014-02-05T21:29:59Z': {0: 0.34,},
     '2014-02-10T20:59:03Z': {0: 0.34,},
     '2014-02-17T21:55:12Z': {0: 0.34,},
     '2014-03-02T13:33:35Z': {0: 6.215, 1:FIVEK_DIST, 2:FIVEK_DIST, 3:FIVEK_DIST, 4:FIVEK_DIST, 5:FIVEK_DIST, 6:FIVEK_DIST, 7:FIVEK_DIST, 8:FIVEK_DIST,},
     '2014-03-06T20:54:47Z': {0: 0.5,},
     '2014-03-07T11:33:19Z': {0: 2.25,},
     '2014-03-09T13:05:56Z': {0: 10.0,},
     '2014-03-13T20:25:57Z': {0: 7.0,},
     '2014-03-30T11:00:56Z': {0: 10.75, 1:8.5, 2:10.0, 4:7.5, 6:6.7},
     '2014-04-03T10:29:09Z': {0: 3.3,},
     '2014-04-05T12:51:31Z': {0: 6.215,},
     '2014-04-10T10:23:09Z': {0: 3.3,},
     '2014-04-12T11:32:37Z': {0: [4.0, 2747]},
     '2014-04-12T13:00:02Z': {0: FIVEK_DIST},
     '2014-04-13T12:21:19Z': {0: 10.0},
     '2014-04-22T10:17:38Z': {0: 3.3},
     '2014-04-27T13:28:03Z': {0: [6.215, (55*60 + 35)]},
     '2014-05-03T11:02:10Z': {0: 3.92*1.028, 1:4.76*1.028, 2:5.48*1.028, 3:6.81*1.028, 4:4.26*1.028, 5:5.01*1.028},
     '2014-05-10T11:30:04Z': {0: 15.34*1.05, 1:1.46*1.05, 2:12.77*1.05},
     '2014-05-17T13:03:28Z': {0: 9.0},
     '2014-05-19T09:24:24Z': {0: 6.0},
     '2014-06-01T12:30:11Z': {0: [8/METERS_PER_MILE, (33*60 + 47)]},
     '2014-06-07T10:18:03Z': {0: 4.0},
     '2014-06-07T13:01:45Z': {0: FIVEK_DIST},
     '2014-06-08T09:32:54Z': {0: [13.68, 60*60+53*60+51+120+60]},
     '2014-06-09T08:56:45Z': {0: 6.0},
     '2014-06-14T10:02:09Z': {0: 5.0},
     '2014-06-14T13:01:16Z': {0: FIVEK_DIST},
     '2014-06-16T23:00:04Z': {0: 5.0},
     '2014-06-19T11:02:47Z': {0: 6.0},
     '2014-06-20T10:04:45Z': {0: 4.7},
     '2014-06-21T10:17:10Z': {0: 4.0},
     '2014-06-21T21:30:16Z': {0: 10/METERS_PER_MILE},
     '2014-06-22T11:03:23Z': {0: [17.77+0.25, (3*60*60+39*60)]},
     '2014-06-23T23:00:01Z': {0: 10/METERS_PER_MILE},
     '2014-06-26T11:02:29Z': {0: 5.8},
     '2014-06-27T09:03:31Z': {0: 6.5},
     '2014-06-28T12:17:47Z': {0: 2.0},
     '2014-06-28T13:06:02Z': {0: 4.0},
     '2014-06-29T13:00:10Z': {0: FIVEK_DIST},
     '2014-06-29T21:00:01Z': {0: FIVEK_DIST},
     '2014-06-30T23:00:04Z': {0: FIVEK_DIST},
     '2014-07-03T10:29:03Z': {0: 6.5},
     '2014-07-04T12:31:03Z': {0: 4.0},
     '2014-07-04T13:08:05Z': {0: [1.05, 12*60]},
     '2014-07-07T23:00:04Z': {0: FIVEK_DIST},
     '2014-07-07T23:26:55Z': {0: [1.06, 11*60+49]},
     '2014-07-10T10:06:21Z': {0: 6.5},
     '2014-07-11T10:02:01Z': {0: 6.},
     '2014-07-18T10:26:13Z': {0: 6.5},
     '2014-07-19T13:00:06Z': {0: 4.0},
     '2014-07-21T23:00:01Z': {0: FIVEK_DIST},
     '2014-07-24T10:35:21Z': {0: 6.5},
     '2014-07-25T11:41:52Z': {0: 3},
     '2014-07-26T09:28:10Z': {0: [10.3, (60*60 + 27*60 + 22)]},
     '2014-07-27T10:47:02Z': {0: 26.3},
     '2014-07-28T23:00:04Z': {0: [FIVEK_DIST, (20*60 + 48)]},
     '2014-07-31T10:17:27Z': {0: [6.5, (3600 + 6*60 + 23 + 60 + 30)]},
     '2014-08-02T13:20:03Z': {0: 4.0},
     '2014-08-04T23:00:04Z': {0: 5.0},
     '2014-08-07T22:35:01Z': {0: [FIVEK_DIST, (19*60 + 42)]},
     '2014-08-09T11:00:04Z': {0: 50./METERS_PER_MILE/3., 1:50./METERS_PER_MILE/3., 2:0., 3:50./METERS_PER_MILE/3.},
     '2014-08-14T10:06:52Z': {0: 6.5},
     '2014-08-17T12:00:04Z': {0: [10/METERS_PER_MILE, 41*60+35]},
     '2014-08-17T12:47:51Z': {0: [1.677/METERS_PER_MILE, 11*60+17]},
     '2014-08-21T10:07:00Z': {0: 6.5},
     '2014-08-22T10:02:59Z': {0: 6.5},
     '2014-08-23T10:17:14Z': {0: [6.5, 68*60+19]},
     '2014-08-24T12:29:58Z': {0: FIVEK_DIST},
     '2014-08-25T10:33:12Z': {0: 0.22},
     '2014-08-29T11:00:57Z': {0: 6.5},
     '2014-08-30T13:40:01Z': {0: 1.0},
     '2014-09-05T10:36:41Z': {0: 6.5},
     '2014-09-07T12:59:56Z': {0: 10/METERS_PER_MILE},
     '2014-09-07T13:46:47Z': {0: [1893.6400000/1609, 878]},
     '2014-09-12T11:17:57Z': {0: 6.5},
     '2014-09-18T11:08:58Z': {0: 6.0},
     '2014-09-20T12:37:01Z': {0: 10/METERS_PER_MILE},
     '2014-09-21T13:01:19Z': {0: MARATHON_DISTANCE_MI/2.},
     '2014-09-25T11:01:00Z': {0: 6.5},
     '2014-09-28T11:00:39Z': {1: [6.0, 60*60+45], 5: [19.38+0.061, 5*60*60+10*60]},
     '2014-10-02T10:58:40Z': {0: 6.5},
     '2014-10-04T12:30:02Z': {0: MARATHON_DISTANCE_MI/2.},
     '2014-10-09T11:05:46Z': {0: 6.5},
     '2014-10-10T10:58:18Z': {0: 6.5},
     '2014-10-11T12:02:42Z': {0: 50./METERS_PER_MILE/3., 1: 50/METERS_PER_MILE/3., 2: 50/METERS_PER_MILE/3.},
     '2014-10-15T10:58:14Z': {0: 7.8},
     '2014-10-16T20:26:12Z': {0: 6.5},
     '2014-10-17T11:19:12Z': {0: 5.5},
     '2014-10-19T12:31:24Z': {0: [32.90, 5*60*60+50*60]},
     '2014-10-24T20:11:28Z': {0: 7.0},
     '2014-10-26T13:36:39Z': {0: 5.0},
     '2014-10-27T20:51:00Z': {0: 6.5},
     '2014-10-28T20:40:35Z': {0: 6.5},
     '2014-10-30T20:21:00Z': {0: 6.5},
     '2014-11-01T14:00:02Z': {0: 4/METERS_PER_MILE},
     '2014-11-04T11:15:38Z': {0: 6.5},
     '2014-11-05T23:42:44Z': {0: [5.18, (43*60 + 42 - 4*60 - 13) * 5.18/4.84]},
     '2014-11-07T11:25:56Z': {0: 6.5},
     '2014-11-08T14:10:11Z': {0: 15/METERS_PER_MILE},
     '2014-11-13T11:28:41Z': {0: 6.5},
     '2014-11-16T14:04:01Z': {0: 10/METERS_PER_MILE},
     '2014-11-15T13:33:44Z': {0: 4.0},
     '2014-11-22T11:59:53Z': {0: [50, (10*60*60 + 56*60 + 19)]},
     '2014-12-02T11:57:31Z': {0: 3.2},
     '2014-12-04T11:57:53Z': {0: 6.5},
     '2014-12-11T12:10:09Z': {0: 6.5},
     '2014-12-13T13:08:20Z': {0: 6.5},
     '2014-12-18T12:07:21Z': {0: 6.5},
     '2014-12-20T14:32:00Z': {0: FIVEK_DIST},
     '2015-01-02T12:52:56Z': {0: 6.5},
     '2015-01-06T12:14:18Z': {0: 6.5},
     '2015-01-09T12:41:06Z': {0: 6.5},
     '2015-01-11T16:00:01Z': {0: FIVEK_DIST},
     '2015-01-15T12:27:59Z': {0: 6.5},
     '2015-01-17T13:21:42Z': {0: 10.0},
     '2015-03-01T13:30:53Z': {0: FIVEK_DIST, 1:FIVEK_DIST, 2:FIVEK_DIST, 3:FIVEK_DIST,
                              4:FIVEK_DIST, 5:FIVEK_DIST, 6:FIVEK_DIST, 7:FIVEK_DIST,
                              8:1.14, 9:(FIVEK_DIST-1.14), 10:FIVEK_DIST},
     '2015-03-20T13:59:53Z': {0: 6.5},
     '2015-03-23T14:53:00Z': {0: 7.6},
     '2015-03-24T13:04:37Z': {0: 6.5},
     '2015-03-25T11:30:07Z': {0: 6.5},
     '2015-03-29T11:02:03Z': {0: 10.75, 1:8.5, 2: [10.0, 11531]},
     '2015-04-02T13:32:26Z': {0: 6.5},
     '2015-04-06T14:35:07Z': {0: 6.5},
     '2015-04-09T18:32:08Z': {0: 6.5},
     '2015-04-11T13:00:01Z': {0: FIVEK_DIST},
     'DUMMY': {0:0.0},}
    # 'time_string': {lap_no: [dist, time_in_sec]},
