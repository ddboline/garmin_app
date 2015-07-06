#!/usr/bin/python
# -*- coding: utf-8 -*-
""" unittests... """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import unittest
import datetime
import dateutil.tz
import glob
import hashlib

GMNFILE = 'tests/test.gmn'
TCXFILE = 'tests/test.tcx'
FITFILE = 'tests/test.fit'
TXTFILE = 'tests/test.txt'

CURDIR = os.path.abspath(os.curdir)
os.sys.path.append(CURDIR)

from garmin_app import garmin_utils,\
                       garmin_file,\
                       garmin_parse,\
                       garmin_cache,\
                       garmin_report,\
                       garmin_summary

from garmin_app.util import run_command

def md5_command(command):
    md5 = run_command(command, single_line=True).split()[0]
    if hasattr(md5, 'decode'):
        md5 = md5.decode()
    return md5

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
        if os.path.exists('temp.pkl.gz'):
            os.remove('temp.pkl.gz')
        for testf in glob.glob('%s/run/cache/test.*' % CURDIR):
            if os.path.exists(testf):
                os.remove(testf)

    def test_gmn_to_gpx(self):
        """ test gmn_to_gpx converter """
        outfile = garmin_utils.convert_gmn_to_gpx(GMNFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = md5_command('tail -n186 %s | md5sum' % outfile)
        self.assertEqual(md5, '93e68a7fcc0e6b41037e16d3f3c59baa')

        outfile = garmin_utils.convert_gmn_to_gpx(TCXFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        if hasattr(md5, 'decode'):
            md5 = md5.decode()
        md5 = md5_command('tail -n740 %s | md5sum' % outfile)
        self.assertEqual(md5, '3e7ab7d5dc77a6e299596d615226ff0b')

        outfile = garmin_utils.convert_gmn_to_gpx(FITFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = md5_command('tail -n1246 %s | md5sum' % outfile)
        self.assertEqual(md5, '47b9208c4ce3fed1c2da3da0ece615c1')

        outfile = garmin_utils.convert_gmn_to_gpx(TXTFILE)
        self.assertEqual(None, outfile)

    def test_fit_to_tcx(self):
        """ test fit_to_tcx converter """
        self.assertFalse(garmin_utils.convert_fit_to_tcx(GMNFILE))
        self.assertFalse(garmin_utils.convert_fit_to_tcx(TCXFILE))
        outfile = garmin_utils.convert_fit_to_tcx(FITFILE)
        self.assertEqual('/tmp/temp.tcx', outfile)
        md5 = md5_command('cat %s | md5sum' % outfile)
        self.assertEqual(md5, 'd96c38457f8bc1b6782bae9f9b02fe5a')

    def test_gmn_to_xml(self):
        """ test gmn to xml conversion"""
        for testf in TCXFILE, FITFILE:
            self.assertEqual(testf, garmin_utils.convert_gmn_to_xml(testf))
        ### the xml output of garmin_dump uses the local timezone,
        ### don't run the test if localtimezone isn't EST
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            outfile = garmin_utils.convert_gmn_to_xml(GMNFILE)
            md5 = md5_command('cat %s | md5sum' % outfile)
            self.assertEqual(md5, 'c941a945ec3a2f75f72d426b57ff3b57')

    def test_read_txt(self):
        """ read text format """
        gfile = garmin_parse.GarminParse(filename=TXTFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'txt')
        self.assertEqual(gfile.begin_datetime.date(),
                         datetime.date(year=2013, month=1, day=16))


    def test_read_xml(self):
        """ read xml format """
        gfile = garmin_parse.GarminParse(filename=GMNFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'gmn')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2011,
                         month=5, day=7))

    def test_read_tcx(self):
        """ read tcx format """
        gfile = garmin_parse.GarminParse(filename=TCXFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'tcx')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2012,
                         month=11, day=5))

    def test_read_fit(self):
        """ read garmin fit format """
        gfile = garmin_parse.GarminParse(filename=FITFILE)
        self.assertTrue(gfile.filetype == 'fit')
        gfile.read_file()
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2014,
                         month=1, day=12))

    def test_cache_dataframe_xml(self):
        """ test cache dump xml to dataframe """
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            gsum = garmin_summary.GarminSummary(GMNFILE)
            gfile = gsum.read_file()
            gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint,\
                    gfile.points).dataframe
            gdf.to_csv('temp.xml.point.csv', index=False)
            md5 = md5_command('cat temp.xml.point.csv | md5sum')
            self.assertEqual(md5, '4f574433d75f4c5406babc81997f719c')
            gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap,
                                               gfile.laps).dataframe
            gdf.to_csv('temp.xml.lap.csv', index=False)
            md5 = md5_command('cat temp.xml.lap.csv | md5sum')
            self.assertEqual(md5, '1a18d3b5b06368a13efb6e00dd0a718c')
            gdf = garmin_cache.GarminDataFrame(garmin_summary.GarminSummary,
                                               [gsum]).dataframe
            gdf.to_csv('temp.fit.sum.csv', index=False)
            md5 = md5_command('cat temp.fit.sum.csv | md5sum')
            self.assertEqual(md5, 'b83e146680aa2583f9f1650c5a709b6a')

    def test_cache_dataframe_tcx(self):
        """ test cache dump tcx to dataframe """
        gsum = garmin_summary.GarminSummary(TCXFILE)
        gfile = gsum.read_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint,
                                           gfile.points).dataframe
        gdf.to_csv('temp.tcx.point.csv', index=False)
        md5 = md5_command('cat temp.tcx.point.csv | md5sum')
        self.assertEqual(md5, '3bb1db7d72096006e3cecdb719c55706')
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap,
                                           gfile.laps).dataframe
        gdf.to_csv('temp.tcx.lap.csv', index=False)
        md5 = md5_command('cat temp.tcx.lap.csv | md5sum')
        self.assertEqual(md5, '982ea8e4949c75f17926cec705882de1')
        gdf = garmin_cache.GarminDataFrame(garmin_summary.GarminSummary,
                                           [gsum]).dataframe
        gdf.to_csv('temp.fit.sum.csv', index=False)
        md5 = md5_command('cat temp.fit.sum.csv | md5sum')
        self.assertEqual(md5, '26856b7d8c53ba8f11e75f49295c5311')

    def test_cache_dataframe_fit(self):
        """ test cache dump fit to dataframe """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gfile = gsum.read_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint,
                                           gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False)
        md5 = md5_command('cat temp.fit.point.csv | md5sum')
        self.assertEqual(md5, '0331e497bb967376401a030654146fe7')
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap,
                                           gfile.laps).dataframe
        gdf.to_csv('temp.fit.lap.csv', index=False)
        md5 = md5_command('cat temp.fit.lap.csv | md5sum')
        self.assertEqual(md5, '7597faf3ade359c193e7fb07607693c7')
        gdf = garmin_cache.GarminDataFrame(garmin_summary.GarminSummary,
                                           [gsum]).dataframe
        gdf.to_csv('temp.fit.sum.csv', index=False)
        md5 = md5_command('cat temp.fit.sum.csv | md5sum')
        self.assertEqual(md5, 'a70326f6c022c149f2c20ad070d24130')

    def test_pickle_fit(self):
        """ test cache dump pickle to dataframe """
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gcache = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz'
                                          % CURDIR,
                                          cache_directory='%s/run/cache'
                                          % CURDIR)
        gcache.write_pickle_object_to_file(gfile)
        del gfile

        gfile = gcache.read_pickle_object_in_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint,
                                           gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False)
        md5 = md5_command('cat temp.fit.point.csv | md5sum')
        self.assertEqual(md5, '0331e497bb967376401a030654146fe7')

    def test_garmin_summary(self):
        """ test GarminSummary.__repr__ """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        output = gsum.__repr__()
        mstr = hashlib.md5()
        mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'f73293da4f5d64545ad4a1d5a1efb283')

    def test_garmin_file_report_txt(self):
        """ test GarminReport.file_report_txt """
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.file_report_txt(gfile)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'dc49eed73bf44c1b5d5c2444a59bec96')

    def test_garmin_file_report_html(self):
        """ test GarminReport.file_report_html """
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gr_ = garmin_report.GarminReport()
        script_path = CURDIR
        options = {'script_path': script_path}
        html_path = gr_.file_report_html(gfile, copy_to_public_html=False,
                                        **options)
        file_md5 = [['index.html', '548581a142811d412dbf955d2e5372aa']]
        for fn_, fmd5 in file_md5:
            md5 = garmin_utils.get_md5('%s/%s' % (html_path, fn_))
            if hasattr(md5, 'decode'):
                md5 = md5.decode()
            self.assertEqual(md5, fmd5)

    def test_garmin_total_summary_report_txt(self):
        """ test GarminReport.total_summary_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.total_summary_report_txt(gsum, sport='running')
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '9f5aa437a6e8bbe6ecd25a088b634018')

    def test_garmin_day_summary_report_txt(self):
        """ test GarminReport.day_summary_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.day_summary_report_txt(gsum, sport='running',
                                           cur_date=gsum.begin_datetime.date())
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'b05ddcddc03a64b650a75ad397037d00')

    def test_garmin_day_average_report_txt(self):
        """ test GarminReport.day_average_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.day_average_report_txt(gsum, sport='running',
                                           number_days=1)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '59c50d1eff34a78619e9f37e45445535')

    def test_garmin_week_summary_report_txt(self):
        """ test GarminReport.week_summary_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        ic_ = gsum.begin_datetime.isocalendar()
        output = gr_.week_summary_report_txt(gsum, sport='running',
                                            isoyear=ic_[0], isoweek=ic_[1],
                                            number_in_week=1,
                                            date=gsum.begin_datetime)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'e538e1b1abd954083c9cc19e14d04315')

    def test_garmin_week_average_report_txt(self):
        """ test GarminReport.week_average_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.week_average_report_txt(gsum, sport='running',
                                            number_of_weeks=1)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '4b649d4c617128138a1540c9dc2e1a09')

    def test_garmin_month_summary_report_txt(self):
        """ test GarminReport.month_summary_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.month_summary_report_txt(gsum, sport='running',
                                             year=gsum.begin_datetime.year,
                                             month=gsum.begin_datetime.month,
                                             number_in_month=1)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'd2a1204e0374c7e83c450a1ae4ce3981')

    def test_garmin_month_average_report_txt(self):
        """ test GarminReport.month_average_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        output = gr_.month_average_report_txt(gsum, sport='running',
                                             number_of_months=1)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '08a90d3c2e16ba2aafb4403e3ed69824')

    def test_garmin_year_summary_report_txt(self):
        """ test GarminReport.year_summary_report_txt """
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr_ = garmin_report.GarminReport()
        dt_ = gsum.begin_datetime
        output = gr_.year_summary_report_txt(gsum, sport='running',
                                            year=dt_.year, number_in_year=1)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'b7ab537ea3090fc44276b15bc61577b5')

    def test_garmin_cache_get_summary_list(self):
        """ test GarminCache.get_cache_summary_list """
        gc_ = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR,
                                      cache_directory='%s/run/cache' % CURDIR)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        output = (
            '\n'.join(
                '%s' % s for s in sorted(sl_, key=lambda x: x.filename)))\
                .replace('ubuntu', 'ddboline')\
                .replace('/root', '/home/ddboline/setup_files/build')\
                .replace('/home/ddboline/Downloads/backup',
                         '/home/ddboline/setup_files/build')
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), 'bb7da3b34b92ed8b63b4359e265dd3f9')

    def test_cached_gfile(self):
        """ test GarminCache.read_cached_gfile """
        gc_ = garmin_cache.GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR)
        gsum = garmin_summary.GarminSummary(FITFILE)
        gfile = gsum.read_file()
        test1 = '%s' % gfile
        gfname = os.path.basename(gfile.orig_filename)
        gc_.write_cached_gfile(gfile)
        gfile_new = gc_.read_cached_gfile(gfname)
        test2 = '%s' % gfile_new
        self.assertEqual(test1, test2)

    def test_summary_report(self):
        """ test GarminReport.summary_report """
        gc_ = garmin_cache.GarminCache(
            pickle_file='%s/temp.pkl.gz' % CURDIR,
            cache_directory='%s/run/cache' % CURDIR)
        sl_ = gc_.get_cache_summary_list(directory='%s/tests' % CURDIR)
        rp_ = garmin_report.GarminReport(cache_obj=gc_)
        options = {'do_plot': False, 'do_year': False, 'do_month': False,
                   'do_week': False, 'do_day': False, 'do_file': False,
                   'do_sport': None, 'do_update': False, 'do_average': False}
        script_path = CURDIR
        options['script_path'] = script_path
        output = rp_.summary_report(sl_, copy_to_public_html=False, **options)
        mstr = hashlib.md5()
        try:
            mstr.update(output)
        except TypeError:
            mstr.update(output.encode())
        self.assertEqual(mstr.hexdigest(), '022c8b604d32c9297195ad80aef5b73c')


if __name__ == '__main__':
    unittest.main()
