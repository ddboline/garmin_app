#!/usr/bin/python
# -*- coding: utf-8 -*-
""" unittests... """
from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import unittest
import datetime
import dateutil.tz
import glob
import hashlib
import mock
import pytest

from garmin_app.garmin_utils import (convert_gmn_to_gpx, convert_fit_to_tcx, convert_gmn_to_xml,
                                     get_md5, get_md5_old, days_in_month, expected_calories,
                                     read_garmin_file)
from garmin_app.garmin_parse import GarminParse
from garmin_app.garmin_summary import GarminSummary
from garmin_app.garmin_data_frame import GarminDataFrame
from garmin_app.garmin_point import GarminPoint
from garmin_app.garmin_lap import GarminLap
from garmin_app.garmin_cache import (GarminCache, read_pickle_object_in_file,
                                     write_pickle_object_to_file)
from garmin_app.garmin_cache_sql import (GarminCacheSQL, GarminSummaryTable,
                                         _write_postgresql_table)
from garmin_app.garmin_report import GarminReport, print_history_buttons
from garmin_app import garmin_corrections
from garmin_app import garmin_corrections_sql
from garmin_app.garmin_corrections import (list_of_corrected_laps, save_corrections)
from garmin_app.garmin_file import GarminFile
from garmin_app.util import (run_command, OpenPostgreSQLsshTunnel, convert_date, POSTGRESTRING,
                             print_h_m_s, openurl)
from garmin_app import garmin_daemon
from garmin_app import garmin_server

GMNFILE = 'tests/test.gmn'
TCXFILE = 'tests/test.tcx'
FITFILE = 'tests/test.fit'
TXTFILE = 'tests/test.txt'
GPXFILE = 'tests/test.gpx'

GARMINSUMMARYSTR = 'GarminSummary<filename=test.fit, ' + \
                   'begin_datetime=2014-01-12 11:00:05-05:00, ' + \
                   'sport=running, ' + \
                   'total_calories=351, total_distance=5081.34, ' + \
                   'total_duration=1451.55, total_hr_dur=220635.6, ' + \
                   'total_hr_dis=1451.55, number_of_items=1, ' + \
                   'md5sum=b543c34cc80daf234b389e7d2ccbcbad>'

# terrible hack
if os.path.exists('garmin_app_unittests.py'):
    os.chdir('../')

CURDIR = os.path.abspath(os.curdir)
os.sys.path.append(CURDIR)


def md5_command(command):
    """ convenience function """
    md5 = run_command(command, single_line=True, do_popen=True).split()[0]
    if hasattr(md5, 'decode'):
        md5 = md5.decode()
    return md5


def cleanup_pickle():
    """ remove temporary files """
    if os.path.exists('temp.pkl.gz'):
        os.remove('temp.pkl.gz')
    for testf in glob.glob('%s/run/cache/test.*' % CURDIR):
        if os.path.exists(testf):
            os.remove(testf)
    if os.path.exists('json_test'):
        for testf in glob.glob('%s/json_test/*' % CURDIR):
            os.remove(testf)
        run_command('rm -rf json_test')
    if os.path.exists('html'):
        run_command('rm -rf html')


class TestGarminApp(unittest.TestCase):
    """ GarminApp Unittests """

    def setUp(self):
        """ setup """
        if not os.path.exists('%s/run/cache' % CURDIR):
            os.makedirs('%s/run/cache' % CURDIR)

    def tearDown(self):
        """ tear down """
        for csvf in glob.glob('temp.*.*.csv'):
            if os.path.exists(csvf):
                os.remove(csvf)
        cleanup_pickle()

    def test_gmn_to_gpx(self):
        """ test gmn_to_gpx converter """
        outfile = convert_gmn_to_gpx(GMNFILE)
        md5 = md5_command('tail -n186 %s | md5sum' % outfile)
        self.assertEqual(md5, '93e68a7fcc0e6b41037e16d3f3c59baa')
        os.remove(outfile)

        outfile = convert_gmn_to_gpx(TCXFILE)
        if hasattr(md5, 'decode'):
            md5 = md5.decode()
        md5 = md5_command('tail -n740 %s | md5sum' % outfile)
        self.assertEqual(md5, 'e4c286408f261a648bb8815521bc0095')
        os.remove(outfile)

        outfile = convert_gmn_to_gpx(FITFILE)
        md5 = md5_command('tail -n1246 %s | md5sum' % outfile)
        self.assertIn(md5, ['d29f88090e92d4a16b27a609ff3a0d9b'])
        os.remove(outfile)

        outfile = convert_gmn_to_gpx(TXTFILE)
        self.assertEqual(None, outfile)

    def test_fit_to_tcx(self):
        """ test fit_to_tcx converter """
        self.assertFalse(convert_fit_to_tcx(GMNFILE))
        self.assertFalse(convert_fit_to_tcx(TCXFILE))
        outfile = convert_fit_to_tcx(FITFILE)
        md5 = md5_command('cat %s | md5sum' % outfile)
        self.assertIn(md5, ['1c304e508709540ccdf44fd70b3c5dcc', 'd96c38457f8bc1b6782bae9f9b02fe5a'])
        os.remove(outfile)

    def test_gmn_to_xml(self):
        """ test gmn to xml conversion"""
        for testf in TCXFILE, FITFILE:
            self.assertEqual(testf, convert_gmn_to_xml(testf))
        # the xml output of garmin_dump uses the local timezone,
        # don't run the test if localtimezone isn't EST
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            outfile = convert_gmn_to_xml(GMNFILE)
            md5 = md5_command('cat %s | md5sum' % outfile)
            self.assertEqual(md5, 'c941a945ec3a2f75f72d426b57ff3b57')
            os.remove(outfile)

    def test_read_txt(self):
        """ read text format """
        gfile = GarminParse(filename=TXTFILE, filetype='txt', corr_list=['A'])
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'txt')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2013, month=1, day=16))

    def test_read_xml(self):
        """ read xml format """
        gfile = GarminParse(filename=GMNFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'gmn')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2011, month=5, day=7))

    def test_read_tcx(self):
        """ read tcx format """
        gfile = GarminParse(filename=TCXFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'tcx')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2012, month=11, day=5))

    def test_read_fit(self):
        """ read garmin fit format """
        gfile = GarminParse(filename=FITFILE)
        self.assertTrue(gfile.filetype == 'fit')
        gfile.read_file()
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2014, month=1, day=12))

    def test_read_gpx(self):
        gfile = GarminParse(filename=GPXFILE)
        self.assertTrue(gfile.filetype == 'gpx')
        gfile.read_file()
        print(gfile)
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2014, month=1, day=12))

    def test_calculate_speed(self):
        """ read garmin fit format """
        gfile = GarminParse(filename=FITFILE)
        gfile.read_file()
        gfile.calculate_speed()
        mstr = hashlib.md5()
        output = '%s' % gfile.points[0]
        mstr.update(output.encode())
        self.assertIn(mstr.hexdigest(), [
            '73c52b6753bc841dc09936dadac33c9c', '7c67d4fb98b12129b4878d11a2af35ee',
            '53087d6c0777c42c9ff06326ad52ab3c'
        ])
        output = '%s' % gfile.points[-1]
        mstr.update(output.encode())
        self.assertIn(mstr.hexdigest(), [
            '1787d7f8a80634d7919bd37a49f8f65c', '61a3902353b0ecd812d296face1e8c9c',
            'e968dfc99ec804e48be5308ce7e108bc'
        ])
        gfile = GarminParse(filename=FITFILE)
        gfile.read_file()
        gfile.points[1].speed_permi = None
        gfile.calculate_speed()
        self.assertAlmostEqual(12.41778, gfile.points[1].speed_permi, places=4)

    def test_cache_dataframe_xml(self):
        """ test cache dump xml to dataframe """
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            gsum = GarminSummary(GMNFILE)
            gfile = gsum.read_file()
            gdf = GarminDataFrame(garmin_class=GarminPoint, garmin_list=gfile.points).dataframe
            gdf.to_csv('temp.xml.point.csv', index=False, float_format='%.4f')
            md5 = md5_command('cat temp.xml.point.csv | md5sum')
            self.assertIn(md5,
                          ['4f574433d75f4c5406babc81997f719c', 'f57722c0aabd0e87bf10ae3d9aabb707'])
            gdf = GarminDataFrame(garmin_class=GarminLap, garmin_list=gfile.laps).dataframe
            gdf.to_csv('temp.xml.lap.csv', index=False, float_format='%.4f')
            md5 = md5_command('cat temp.xml.lap.csv | md5sum')
            self.assertIn(md5,
                          ['1a18d3b5b06368a13efb6e00dd0a718c', '60d445adb1f0586fda32b3166f44a18f'])
            gdf = GarminDataFrame(garmin_class=GarminSummary, garmin_list=[gsum]).dataframe
            gdf.to_csv('temp.fit.sum.csv', index=False, float_format='%.4f')
            md5 = md5_command('cat temp.fit.sum.csv | md5sum')
            self.assertIn(md5, [
                '4d58abbb5cd604582782595c99f83757', '4aed7300dae1ebc400642cbf87dceac8',
                '4bf114c418e0bf66ead4c31b3a464073'
            ])

    def test_cache_dataframe_tcx(self):
        """ test cache dump tcx to dataframe """
        gsum = GarminSummary(TCXFILE)
        gfile = gsum.read_file()
        gdf = GarminDataFrame(garmin_class=GarminPoint, garmin_list=gfile.points).dataframe
        gdf.to_csv('temp.tcx.point.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.tcx.point.csv | md5sum')
        self.assertEqual(md5, '5ebd5307817c251ae58e48862a633d47')
        gdf = GarminDataFrame(garmin_class=GarminLap, garmin_list=gfile.laps).dataframe
        gdf.to_csv('temp.tcx.lap.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.tcx.lap.csv | md5sum')
        #self.assertEqual(md5, '90402b951f4e677a07b9d04e4af94a18')
        gdf = GarminDataFrame(garmin_class=GarminSummary, garmin_list=[gsum]).dataframe
        gdf.to_csv('temp.fit.sum.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.fit.sum.csv | md5sum')
        self.assertIn(md5, ['ac5e35fea996f62757b6c25d21f543f4', '9de73ef049c7c6c5287bc1fe5c35d501'])

    def test_cache_dataframe_fit(self):
        """ test cache dump fit to dataframe """
        gsum = GarminSummary(FITFILE)
        gfile = gsum.read_file()
        gdf = GarminDataFrame(garmin_class=GarminPoint, garmin_list=gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.fit.point.csv | md5sum')
        self.assertEqual(md5, '9b5dd53949c7f9555d97c4a95be1934e')
        gdf = GarminDataFrame(garmin_class=GarminLap, garmin_list=gfile.laps).dataframe
        gdf.to_csv('temp.fit.lap.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.fit.lap.csv | md5sum')
        #self.assertEqual(md5, 'c3c3ee7f75d11b7c64fa3b854602cdaf')
        gdf = GarminDataFrame(garmin_class=GarminSummary, garmin_list=[gsum]).dataframe
        gdf.to_csv('temp.fit.sum.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.fit.sum.csv | md5sum')
        self.assertIn(md5, ['2cbb419260abb688a930065f7d192186', '2ab4f377f398b9f7db9132bd6e40f02c'])

    def test_cache_dataframe_fit_fill_list(self):
        """ test GarminDataFrame.fill_list """
        gsum = GarminSummary(FITFILE)
        gfile = gsum.read_file()
        gdf = GarminDataFrame(garmin_class=GarminPoint, garmin_list=gfile.points)
        output = '%s' % gdf.fill_list()[0]

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertIn(mstr.hexdigest(), [
            '73c52b6753bc841dc09936dadac33c9c', '53087d6c0777c42c9ff06326ad52ab3c',
            '7c67d4fb98b12129b4878d11a2af35ee'
        ])

    def test_pickle_fit(self):
        """ test cache dump pickle to dataframe """
        gfile = GarminParse(FITFILE)
        gfile.read_file()
        gcache = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR,
            use_sql=False)
        write_pickle_object_to_file(gfile, gcache.pickle_file)
        del gfile

        gfile = read_pickle_object_in_file(gcache.pickle_file)
        gdf = GarminDataFrame(garmin_class=GarminPoint, garmin_list=gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False, float_format='%.4f')
        md5 = md5_command('cat temp.fit.point.csv | md5sum')
        self.assertEqual(md5, '9b5dd53949c7f9555d97c4a95be1934e')

    def test_garmin_summary(self):
        """ test GarminSummary.__repr__ """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        output = '%s' % gsum
        # output = output.replace('begin_datetime=2014-01-12 16:00:05+00:00',
        # 'begin_datetime=2014-01-12 11:00:05-05:00')
        print(output)
        print(GARMINSUMMARYSTR)
        self.assertEqual(output, GARMINSUMMARYSTR)
        mstr = hashlib.md5()
        mstr.update(output.encode())

#        self.assertEqual(mstr.hexdigest(), 'f73293da4f5d64545ad4a1d5a1efb283')

    def test_garmin_file_report_txt(self):
        """ test GarminReport.file_report_txt """
        gfile = GarminParse(FITFILE)
        gfile.read_file()
        gr_ = GarminReport(gfile=gfile)
        output = gr_.file_report_txt()

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'dc49eed73bf44c1b5d5c2444a59bec96')

    def test_garmin_file_report_html(self):
        """ test GarminReport.file_report_html """
        gfile = GarminParse(FITFILE)
        gfile.read_file()
        gr_ = GarminReport(gfile=gfile)
        script_path = CURDIR
        options = {'script_path': '%s/garmin_app' % script_path, 'cache_dir': script_path}
        html_path = gr_.file_report_html(copy_to_public_html=False, options=options)
        file_md5 = [[
            'index.html', [
                '1c1abe181f36a85949974a222cc874df', '548581a142811d412dbf955d2e5372aa',
                '73bb500bed38ef9f2881f11019b7c27c'
            ]
        ]]
        for fn_, fmd5 in file_md5:
            md5 = get_md5('%s/%s' % (html_path, fn_))
            if hasattr(md5, 'decode'):
                md5 = md5.decode()
#            self.assertIn(md5, fmd5)

    def test_garmin_total_summary_report_txt(self):
        """ test GarminReport.total_summary_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        output = gr_.total_summary_report_txt(gsum, sport='running')

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '9f5aa437a6e8bbe6ecd25a088b634018')

    def test_garmin_day_summary_report_txt(self):
        """ test GarminReport.day_summary_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        output = gr_.day_summary_report_txt(
            gsum, sport='running', cur_date=gsum.begin_datetime.date())

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'b05ddcddc03a64b650a75ad397037d00')

    def test_garmin_day_average_report_txt(self):
        """ test GarminReport.day_average_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        self.assertFalse(gr_.day_average_report_txt(gsum, number_days=0))
        output = gr_.day_average_report_txt(gsum, sport='running', number_days=1)

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '59c50d1eff34a78619e9f37e45445535')

    def test_garmin_week_summary_report_txt(self):
        """ test GarminReport.week_summary_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        ic_ = gsum.begin_datetime.isocalendar()
        output = gr_.week_summary_report_txt(
            gsum,
            sport='running',
            isoyear=ic_[0],
            isoweek=ic_[1],
            number_in_week=1,
            date=gsum.begin_datetime)

        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'e538e1b1abd954083c9cc19e14d04315')

    def test_garmin_week_average_report_txt(self):
        """ test GarminReport.week_average_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        output = gr_.week_average_report_txt(gsum, sport='running', number_of_weeks=1)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '4b649d4c617128138a1540c9dc2e1a09')

    def test_garmin_month_summary_report_txt(self):
        """ test GarminReport.month_summary_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        output = gr_.month_summary_report_txt(
            gsum,
            sport='running',
            year=gsum.begin_datetime.year,
            month=gsum.begin_datetime.month,
            number_in_month=1)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'd2a1204e0374c7e83c450a1ae4ce3981')

    def test_garmin_month_average_report_txt(self):
        """ test GarminReport.month_average_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        output = gr_.month_average_report_txt(gsum, sport='running', number_of_months=1)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '08a90d3c2e16ba2aafb4403e3ed69824')

    def test_garmin_year_summary_report_txt(self):
        """ test GarminReport.year_summary_report_txt """
        gsum = GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = GarminReport()
        dt_ = gsum.begin_datetime
        output = gr_.year_summary_report_txt(gsum, sport='running', year=dt_.year, number_in_year=1)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'b7ab537ea3090fc44276b15bc61577b5')

    def test_garmin_cache(self):
        """ test GarminCache.get_cache_summary_list """
        gc_ = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR,
            cache_read_fn=read_pickle_object_in_file,
            cache_write_fn=write_pickle_object_to_file,
            use_sql=False)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        output = '\n'.join('%s' % s for s in sorted(sl_.values(), key=lambda x: x.filename))
        test_output = open('tests/test_cache_summary.out', 'rt').read().strip()

        test_output0 = test_output.replace('10:43:08-05:00', '11:43:08-04:00')

        mstr = hashlib.md5()
        mstr.update(output.encode())
        print(output)
        #        print(test_output)
        self.assertIn(output, [test_output, test_output0])

        sqlite_str = 'sqlite:///%s/run/cache/test.db' % CURDIR
        gc_ = GarminCacheSQL(sql_string=sqlite_str)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        output = '\n'.join('%s' % s for s in sorted(sl_.values(), key=lambda x: x.filename))
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertIn(mstr.hexdigest(), [
            'c06f13236f9abed0723e4af7537ca3d4', 'a59c8ee120e789eda36e0cc8592ffce1',
            '35475bfdd07e72c9cd3988c83a07b083', 'f1749a2ec48d1ca814b570d2bf36d587'
        ])

        gc0 = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR,
            use_sql=False)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        sqlite_str = 'sqlite:///%s/run/cache/test.db' % CURDIR
        gc1 = GarminCacheSQL(sql_string=sqlite_str, garmin_cache=gc0, summary_list=sl_)
        output = '\n'.join('%s' % s
                           for s in sorted(gc1.summary_list.values(), key=lambda x: x.filename))
        mstr = hashlib.md5()
        mstr.update(output.encode())
#        self.assertIn(mstr.hexdigest(), [
#            '06465ba08d19d59c963e542bc19f12b7', 'a59c8ee120e789eda36e0cc8592ffce1',
#            '34605a1d755eda499022946e46d46c1a', '9fbf84e57a513d875f471fbcabe20e22',
#            '9e23c7a7bc3c436ef319a5a3d1003264'
#        ])

        with OpenPostgreSQLsshTunnel(port=5435, do_tunnel=True) as pport:
            postgre_str = '%s:%d/test_garmin_summary' % (POSTGRESTRING, pport)
            gc_ = GarminCacheSQL(sql_string=postgre_str)
            sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
            output = '\n'.join('%s' % s for s in sorted(sl_.values(), key=lambda x: x.filename))
            print(output)
            mstr = hashlib.md5()
            mstr.update(output.encode())
            #self.assertIn(mstr.hexdigest(), [
                #'c06f13236f9abed0723e4af7537ca3d4', 'a59c8ee120e789eda36e0cc8592ffce1',
                #'35475bfdd07e72c9cd3988c83a07b083', '34605a1d755eda499022946e46d46c1a',
                #'9fbf84e57a513d875f471fbcabe20e22', 'f1749a2ec48d1ca814b570d2bf36d587',
                #'9e23c7a7bc3c436ef319a5a3d1003264'
            #])

        with OpenPostgreSQLsshTunnel(port=5436, do_tunnel=True) as pport:
            postgre_str = '%s:%d/test_garmin_summary' % (POSTGRESTRING, pport)
            gc_ = GarminCache(
                pickle_file='%s/temp.pkl.gz' % CURDIR,
                cache_directory='%s/run/cache' % CURDIR,
                cache_read_fn=read_pickle_object_in_file,
                cache_write_fn=write_pickle_object_to_file,
                use_sql=False)
            sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
            sl_ = _write_postgresql_table(
                sl_, get_summary_list=True, dbname='test_garmin_summary', port=pport)
            sl_ = _write_postgresql_table(sl_, dbname='test_garmin_summary', port=pport)
            print(len(sl_))
            output = '\n'.join('%s' % s for s in sorted(sl_.values(), key=lambda x: x.filename))
            gc_ = GarminCacheSQL(sql_string=postgre_str)
            gc_.delete_table()
            mstr = hashlib.md5()
            mstr.update(output.encode())
#            self.assertIn(mstr.hexdigest(), [
#                '06465ba08d19d59c963e542bc19f12b7', '34605a1d755eda499022946e46d46c1a',
#                '9fbf84e57a513d875f471fbcabe20e22', '9e23c7a7bc3c436ef319a5a3d1003264'
#            ])

        gc_ = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR,
            use_sql=False)
        gsum = GarminSummary(FITFILE)
        gfile = gsum.read_file()
        gc_.write_cached_gfile(gfile)
        gfile_new = gc_.read_cached_gfile(gfbname=gfile.filename)
        self.assertEqual(gfile, gfile_new)

        gc_ = GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR, use_sql=False)
        gfile_new = gc_.read_cached_gfile(gfbname=gfile.filename)
        self.assertEqual(gfile_new, False)

        gc_ = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_read_fn=read_pickle_object_in_file,
            cache_write_fn=write_pickle_object_to_file,
            cache_directory='%s/run/cache' % CURDIR,
            use_sql=False)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        rp_ = GarminReport(cache_obj=gc_)
        options = {
            'do_plot': False,
            'do_year': False,
            'do_month': False,
            'do_week': False,
            'do_day': False,
            'do_file': False,
            'do_sport': None,
            'do_update': False,
            'do_average': False
        }
        script_path = CURDIR
        options['script_path'] = '%s/garmin_app' % script_path
        options['cache_dir'] = script_path
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'dd7cc23be0f6f21a6d05782e506cb647')

    def test_summary_report_file(self):
        """ test GarminCache.summary_report """
        gc_ = GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_read_fn=read_pickle_object_in_file,
            cache_write_fn=write_pickle_object_to_file,
            cache_directory='%s/run/cache' % CURDIR,
            use_sql=False)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        rp_ = GarminReport(cache_obj=gc_)
        options = {
            'do_plot': False,
            'do_year': True,
            'do_month': True,
            'do_week': True,
            'do_day': True,
            'do_file': True,
            'do_sport': 'running',
            'do_update': False,
            'do_average': True
        }
        script_path = CURDIR
        options['script_path'] = '%s/garmin_app' % script_path
        options['cache_dir'] = script_path
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '79e43ff052e6a2238f54d7c2cd78b0ad')
        options['do_sport'] = None
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '927f7ac0f1eb04b20ffe78c23bc6936c')
        options['do_sport'] = 'running'
        options['do_week'] = False
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '88d026c8736bef031d84bede447471cc')
        options['do_sport'] = 'running'
        options['do_month'] = False
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '94954edf36e8625143735f8b3e263c6b')
        options = {
            'do_plot': False,
            'do_year': False,
            'do_month': False,
            'do_week': False,
            'do_day': False,
            'do_file': False,
            'do_sport': None,
            'do_update': False,
            'do_average': False,
            'occur': True
        }
        options['script_path'] = '%s/garmin_app' % script_path
        options['cache_dir'] = script_path
        output = rp_.summary_report(sl_, copy_to_public_html=False, options=options)
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '6256eb536104110794d9fc2123a8c104')

    def test_garmin_summary_table(self):
        """ test GarminSummaryTable """
        tmp = '%s' % GarminSummaryTable()
        exp = 'GarminSummaryTable<filename=None, begin_datetime=None, ' + \
              'sport=None, total_calories=None, total_distance=None, ' + \
              'total_duration=None, total_hr_dur=None, total_hr_dis=None, ' + \
              'number_of_items=None, md5sum=None>'
        self.assertEqual(tmp, exp)

    def test_list_of_corrected_laps(self):
        """ test list_of_corrected_laps """
        test_json = {
            u'2011-07-04T08:58:27Z': {
                0: 3.1068559611866697
            },
            u'2012-03-13T18:21:11Z': {
                0: 0.362
            },
            u'DUMMY': {
                0: 0.0
            }
        }
        save_corrections(test_json, json_path='json_test', json_file='test.json')
        tmp = list_of_corrected_laps(json_path='json_test', json_file='test.json')
        md5_ = get_md5('json_test/test.json')
        self.assertEqual(tmp, test_json)
        self.assertIn(md5_,
                      ['a6ff6819f6c47a0af8334fae36c49b2d', '11bfd6af403c3fa8b38203493d0e1c4e'])

    def test_garmin_file(self):
        """ test GarminFile """
        gf_ = GarminFile(filename=FITFILE, filetype='fit')
        tmp = '%s' % gf_
        test = 'GarminFile<filename=test.fit, filetype=fit, ' + \
               'begin_datetime=None, sport=None, total_calories=0, ' + \
               'total_distance=0, total_duration=0, total_hr_dur=0, ' + \
               'total_hr_dis=0>'
        self.assertEqual(tmp, test)

    def test_garmin_lap_fit(self):
        """ test GarminLap """
        gfile = GarminParse(filename=FITFILE)
        gfile.read_file()
        gl_ = gfile.laps[0]
        opts = {key: getattr(gl_, key) for key in dir(gl_)}
        gl_ = GarminLap(**opts)
        tmp = '%s' % gl_
        test = 'GarminLap<lap_type=None, lap_index=0, ' + \
               'lap_start=2014-01-12 16:00:05, lap_duration=1451.55, ' + \
               'lap_distance=5081.34, lap_trigger=Manual, ' + \
               'lap_max_speed=4.666, lap_calories=351, lap_avg_hr=152, ' + \
               'lap_max_hr=160, lap_intensity=Active, lap_number=0, ' + \
               'lap_start_string=2014-01-12T16:00:05Z>'
        print(tmp)
        self.assertEqual(tmp, test)

    def test_garmin_lap_xml(self):
        """ test GarminLap.read_lap_xml """
        gfile = GarminParse(filename=GMNFILE)
        gfile.read_file()
        gl_ = gfile.laps[0]
        opts = {key: getattr(gl_, key) for key in dir(gl_)}
        gl_ = GarminLap(**opts)
        gl_.read_lap_xml(['avg_hr=123', 'max_hr=170'])
        tmp = '%s' % gl_
        test = 'GarminLap<lap_type=1015, lap_index=108, ' + \
               'lap_start=2011-05-07 15:43:08, lap_duration=280.38, ' + \
               'lap_distance=1696.85999, lap_trigger=manual, ' + \
               'lap_max_speed=7.96248627, lap_calories=61, ' + \
               'lap_avg_hr=123, lap_max_hr=170, lap_intensity=active, ' + \
               'lap_number=0, lap_start_string=2011-05-07T15:43:08-04:00>'
        self.assertEqual(tmp, test)

    def test_read_xml_correction(self):
        """ read garmin xml format """
        gfile = GarminParse(filename=GMNFILE, corr_list={'2011-05-07T15:43:08Z': {0: [1.1, 300]}})
        gfile.read_file()
        tmp = '%s' % gfile
        test0 = 'GarminFile<filename=test.gmn, filetype=gmn, ' + \
                'begin_datetime=2011-05-07 15:43:08, sport=biking, ' + \
                'total_calories=61, total_distance=1770.2784, ' + \
                'total_duration=300, total_hr_dur=0, total_hr_dis=0>'
        test1 = test0.replace('total_distance=1770.2784', 'total_distance=1770.2784000000001')
        self.assertTrue(gfile.filetype == 'gmn')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2011, month=5, day=7))
        self.assertIn(tmp, [test0, test1])
        gsum = GarminSummary(filename=GMNFILE, corr_list={'2011-05-07T15:43:08Z': {0: [1.1, 300]}})
        gsum.read_file()
        tmp = '%s' % gsum
        test0 = 'GarminSummary<filename=test.gmn, begin_datetime=' \
                '2011-05-07 10:43:08-05:00, sport=biking, ' \
                'total_calories=61, total_distance=1770.2784, ' \
                'total_duration=300, total_hr_dur=0, total_hr_dis=0, ' \
                'number_of_items=1, md5sum=af6f79ef18f4ec5526d3f987b6f00f9b>'
        test1 = test0.replace('total_distance=1770.2784', 'total_distance=1770.2784000000001')
        test2 = test0.replace('10:43:08-05:00', '11:43:08-04:00')
        test3 = test1.replace('10:43:08-05:00', '11:43:08-04:00')
        print(tmp)
        print(test0)
        print(test1)
        print(test2)
        self.assertIn(tmp, [test0, test1, test2, test3])

    def test_read_tcx_correction(self):
        """ read garmin tcx format """
        gfile = GarminParse(filename=TCXFILE, corr_list={'2012-11-05T11:52:21Z': {0: [4.0, 1050]}})
        gfile.read_file()
        tmp = '%s' % gfile
        test = 'GarminFile<filename=test.tcx, filetype=tcx, ' + \
               'begin_datetime=2012-11-05 11:52:21, sport=biking, ' + \
               'total_calories=285, total_distance=6437.376, ' + \
               'total_duration=1050, total_hr_dur=0, total_hr_dis=0>'
        self.assertTrue(gfile.filetype == 'tcx')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2012, month=11, day=5))
        self.assertEqual(tmp, test)
        gsum = GarminSummary(filename=TCXFILE, corr_list={'2012-11-05T11:52:21Z': {0: [4.0, 1050]}})
        gsum.read_file()
        tmp = '%s' % gsum
        test = 'GarminSummary<filename=test.tcx, begin_datetime=' + \
               '2012-11-05 06:52:21-05:00, sport=biking, total_calories=285, ' + \
               'total_distance=6437.376, total_duration=1050, ' + \
               'total_hr_dur=0, total_hr_dis=0, number_of_items=1, ' + \
               'md5sum=eaa1e1a2bc26b1145a046c39f31b4024>'
        # tmp = tmp.replace('begin_datetime=2012-11-05 11:52:21+00:00',
        # 'begin_datetime=2012-11-05 06:52:21-05:00')
        print(tmp)
        print(test)
        self.assertEqual(tmp, test)

    def test_print_history_buttons(self):
        """ test print_history_buttons """
        self.assertIsNone(print_history_buttons(None))
        self.assertEqual(print_history_buttons(['year']), '')
        test = '<button type="submit" onclick="send_command(' + \
               "'prev 2015 month'" + ');"> 2015 month </button>'
        self.assertEqual(print_history_buttons(['year', '2015 month']), test)

    def test_days_in_month(self):
        """ test days_in_month """
        month = datetime.date.today().month
        year = datetime.date.today().year
        self.assertEqual(days_in_month(), days_in_month(month=month, year=year))
        self.assertEqual(days_in_month(month=12, year=2015), 31)

    def test_expected_calories(self):
        """ test expected_calories """
        self.assertAlmostEqual(expected_calories(), 14.048, places=3)

    def test_get_md5(self):
        """ test get_md5 """
        self.assertEqual(get_md5(FITFILE), get_md5_old(FITFILE))

    def test_read_garmin_file(self):
        """ test read_garmin_file """
        options = {
            'do_plot': False,
            'do_year': False,
            'do_month': False,
            'do_week': False,
            'do_day': False,
            'do_file': False,
            'do_sport': None,
            'do_update': False,
            'do_average': False
        }
        script_path = CURDIR
        options['script_path'] = '%s/garmin_app' % script_path
        options['cache_dir'] = script_path
        self.assertTrue(read_garmin_file(FITFILE, options=options))

        with self.assertRaises(IOError):
            read_garmin_file('NULL', options=options)


def test_run_command():
    """ test run_command """
    cmd = 'echo "HELLO"'
    out = run_command(cmd, do_popen=True, single_line=True).strip()
    assert out == b'HELLO'

    out = run_command(cmd, turn_on_commands=False)
    assert out == cmd


def test_convert_date():
    """ test convert_date """
    import datetime
    assert convert_date('080515') == datetime.date(year=2015, month=8, day=5)


def test_print_h_m_s():
    """ test print_h_m_s """
    assert print_h_m_s(12345) == '03:25:45'


def test_openurl():
    """ test openurl """
    import hashlib
    output = ''.join(openurl('https://httpbin.org/html'))
    output = output.encode(errors='replace')
    mstr = hashlib.md5()
    mstr.update(output)
    output = mstr.hexdigest()
    assert output in ('fefa33a57febcf8a413cc252966670fb', '348369d8bd0d9ae6c4cdfc9e2cfa7e99')

    from requests import HTTPError
    from nose.tools import raises

    @raises(HTTPError)
    def test_httperror():
        """ ... """
        openurl('https://httpbin.org/aspdoifqwpof')

    test_httperror()


def test_garmin_daemon():
    conn = mock.MagicMock()
    msgq = ['year run', '2017 month run', '2017-03 day run', '2017 year run']

    conn.recv.return_value = 'prev 2017 year run'

    garmin_daemon.handle_connection(conn, msgq)

    conn.send.assert_called_once_with('done')

    conn.recv.return_value = ''

    garmin_daemon.handle_connection(conn, msgq)

    conn.recv.return_value = 'prev year'

    garmin_daemon.handle_connection(conn, msgq)

    conn.recv.return_value = 'prev year run'

    garmin_daemon.handle_connection(conn, msgq)


@mock.patch('garmin_app.garmin_cache.pickle')
def test_garmin_cache_pickle_error(mock_pickle):
    b = bytes([0])
    s = str('TEST')
    mock_pickle.load.side_effect = UnicodeDecodeError(s, b, 0, 1, s)

    gfile = GarminParse(FITFILE)
    gfile.read_file()
    gcache = GarminCache(
        pickle_file='%s/temp.pkl.gz' % CURDIR,
        cache_directory='%s/run/cache' % CURDIR,
        use_sql=False)
    write_pickle_object_to_file(gfile, gcache.pickle_file)
    del gfile

    result = read_pickle_object_in_file(gcache.pickle_file)

    assert result is None


@mock.patch('garmin_app.garmin_cache.os')
def test_garmin_cache_makedir(mock_os):
    mock_path = mock.MagicMock()
    mock_os.path = mock_path
    mock_path.exists.return_value = False

    gcache = GarminCache(
        pickle_file='%s/temp.pkl.gz' % CURDIR,
        cache_directory='%s/run/cache' % CURDIR,
        use_sql=False)

    mock_os.makedirs.assert_called_once_with('%s/run/cache' % CURDIR)


@mock.patch('garmin_app.garmin_cache.read_pickle_object_in_file')
def test_read_cached_gfile(mock_func):
    mock_func.side_effect = ValueError()

    gc_ = GarminCache(
        pickle_file='%s/temp.pkl.gz' % CURDIR,
        cache_directory='%s/run/cache' % CURDIR,
        use_sql=False)
    gsum = GarminSummary(FITFILE)
    gfile = gsum.read_file()
    gc_.write_cached_gfile(gfile)
    gfile_new = gc_.read_cached_gfile(gfbname=gfile.filename)
    assert gfile_new is not False


def test_garmin_corrections():
    test_json = {
        u'2011-07-04T08:58:27Z': {
            0: 3.1068559611866697
        },
        u'2012-03-13T18:21:11Z': {
            0: 0.362
        },
        u'DUMMY': {
            0: 0.0
        }
    }
    save_corrections(test_json, json_path='json_test', json_file='test.json')
    tmp = list_of_corrected_laps(json_path='json_test', json_file='test.json')
    assert garmin_corrections.get_list_of_corrected_laps() == tmp
    cleanup_pickle()

@mock.patch('garmin_app.garmin_corrections_sql.sessionmaker')
@mock.patch('garmin_app.garmin_corrections_sql.create_engine')
def test_garmin_corrections_sql(mock_create_engine, mock_sessionmaker):
    tmp = '%s' % garmin_corrections_sql.GarminCorrectionsLaps()
    assert tmp == 'GarminCorrectionsLaps<start_time=None, lap_number=None, ' \
        'distance=None, duration=None>'

    mock_engine = mock.MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_session = mock.MagicMock()
    mock_session2 = mock.MagicMock()
    mock_sessionmaker.return_value.return_value = mock_session
    mock_session.query.return_value = mock_session2
    mock_row = mock.MagicMock()
    mock_row.dur = 5.0
    mock_row.duration = 5.0
    mock_row.dis = 5.0
    mock_row.start_time = datetime.datetime(2017, 5, 1, 13)
    mock_session2.all.return_value = [mock_row]
    g = garmin_corrections_sql.GarminCorrectionsSQL(garmin_corrections_={'TEST': 'TEST'})
    assert g.garmin_corrections_ == {'TEST': 'TEST'}

    t = g.read_sql_table()
    assert t['TEST'] == 'TEST'
    assert '2017-05-01T13:00:00Z' in t


@mock.patch('garmin_app.garmin_daemon.exit')
@mock.patch('garmin_app.garmin_daemon.handle_connection')
@mock.patch('garmin_app.garmin_daemon.OpenSocketConnection')
@mock.patch('garmin_app.garmin_daemon.OpenUnixSocketServer')
def test_garmin_daemon_server_thread(mock_server, mock_con, mock_handle, mock_exit):
    mock_sock = mock.MagicMock()
    mock_server.__enter__.return_value = mock_sock
    mock_conn = mock.MagicMock()
    mock_con.__enter__.return_value = mock_conn
    mock_handle.side_effect = KeyboardInterrupt()
    mock_exit.side_effect = Exception()

    with pytest.raises(Exception):
        garmin_daemon.server_thread()


@mock.patch('garmin_app.garmin_server.mp')
def test_garmin_server(mock_mp):
    mock_manager = mock.MagicMock()
    mock_mp.Manager.return_value = mock_manager
    mock_mp.Process.return_value = mock_manager

    with garmin_server.garmin_server() as g:
        g.start.assert_called_once()
    mock_manager.join.assert_called_once()


if __name__ == '__main__':
    unittest.main()
