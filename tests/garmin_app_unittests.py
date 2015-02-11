#!/usr/bin/python
# -*- coding: utf-8 -*-

''' unittests... '''

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

from garmin_app.util import run_command, datetimefromstring

class TestGarminApp(unittest.TestCase):

    def setUp(self):
        if not os.path.exists('%s/run/cache' % CURDIR):
            os.makedirs('%s/run/cache' % CURDIR)
        pass

    def tearDown(self):
        for f in glob.glob('temp.*.*.csv'):
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists('temp.pkl.gz'):
            os.remove('temp.pkl.gz')
        for f in glob.glob('%s/run/cache/test.*' % CURDIR):
            if os.path.exists(f):
                os.remove(f)
        pass

    def test_gmn_to_gpx(self):
        ''' test gmn_to_gpx converter '''
        outfile = garmin_utils.convert_gmn_to_gpx(GMNFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n186 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, '93e68a7fcc0e6b41037e16d3f3c59baa')

        outfile = garmin_utils.convert_gmn_to_gpx(TCXFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n740 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, '3e7ab7d5dc77a6e299596d615226ff0b')

        outfile = garmin_utils.convert_gmn_to_gpx(FITFILE)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n1246 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, 'e06a6217293b218b8ca1e4dbf07174ce')

        outfile = garmin_utils.convert_gmn_to_gpx(TXTFILE)
        self.assertEqual(None, outfile)

    def test_fit_to_tcx(self):
        ''' test fit_to_tcx converter '''
        self.assertFalse(garmin_utils.convert_fit_to_tcx(GMNFILE))
        self.assertFalse(garmin_utils.convert_fit_to_tcx(TCXFILE))
        outfile = garmin_utils.convert_fit_to_tcx(FITFILE)
        self.assertEqual('/tmp/temp.tcx', outfile)
        md5 = run_command('cat %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, '1c304e508709540ccdf44fd70b3c5dcc')

    def test_gmn_to_xml(self):
        for f in TCXFILE, FITFILE:
            self.assertEqual(f, garmin_utils.convert_gmn_to_xml(f))
        ### the xml output of garmin_dump uses the local timezone, don't run the test if localtimezone isn't EST
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            outfile = garmin_utils.convert_gmn_to_xml(GMNFILE)
            md5 = run_command('cat %s | md5sum' % outfile, do_popen=True).read().split()[0]
            self.assertEqual(md5, 'c941a945ec3a2f75f72d426b57ff3b57')

    def test_read_txt(self):
        gfile = garmin_parse.GarminParse(filename=TXTFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'txt')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2013, month=1, day=16))


    def test_read_xml(self):
        gfile = garmin_parse.GarminParse(filename=GMNFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'gmn')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2011, month=5, day=7))

    def test_read_tcx(self):
        gfile = garmin_parse.GarminParse(filename=TCXFILE)
        gfile.read_file()
        self.assertTrue(gfile.filetype == 'tcx')
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2012, month=11, day=5))

    def test_read_fit(self):
        gfile = garmin_parse.GarminParse(filename=FITFILE)
        self.assertTrue(gfile.filetype == 'fit')
        gfile.read_file()
        self.assertEqual(gfile.begin_datetime.date(), datetime.date(year=2014, month=1, day=12))

    def test_cache_dataframe_xml(self):
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            gfile = garmin_parse.GarminParse(GMNFILE)
            gfile.read_file()
            gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint, gfile.points).dataframe
            gdf.to_csv('temp.xml.point.csv', index=False)
            md5 = run_command('cat temp.xml.point.csv | md5sum', do_popen=True).read().split()[0]
            self.assertEqual(md5, '4f574433d75f4c5406babc81997f719c')
            gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap, gfile.laps).dataframe
            gdf.to_csv('temp.xml.lap.csv', index=False)
            md5 = run_command('cat temp.xml.lap.csv | md5sum', do_popen=True).read().split()[0]
            self.assertEqual(md5, '1a18d3b5b06368a13efb6e00dd0a718c')

    def test_cache_dataframe_tcx(self):
        gfile = garmin_parse.GarminParse(TCXFILE)
        gfile.read_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint, gfile.points).dataframe
        gdf.to_csv('temp.tcx.point.csv', index=False)
        md5 = run_command('cat temp.tcx.point.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '3bb1db7d72096006e3cecdb719c55706')
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap, gfile.laps).dataframe
        gdf.to_csv('temp.tcx.lap.csv', index=False)
        md5 = run_command('cat temp.tcx.lap.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '982ea8e4949c75f17926cec705882de1')

    def test_cache_dataframe_fit(self):
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint, gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False)
        md5 = run_command('cat temp.fit.point.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '31a1ec7ed186440c28ff6ff052da13f3')
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminLap, gfile.laps).dataframe
        gdf.to_csv('temp.fit.lap.csv', index=False)
        md5 = run_command('cat temp.fit.lap.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '7597faf3ade359c193e7fb07607693c7')

    def test_pickle_fit(self):
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gcache = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR, cache_directory='%s/run/cache' % CURDIR)
        gcache.write_pickle_object_to_file(gfile)
        del gfile

        gfile = gcache.read_pickle_object_in_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint, gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False)
        md5 = run_command('cat temp.fit.point.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '31a1ec7ed186440c28ff6ff052da13f3')

    def test_garmin_summary(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gfile = gsum.read_file()
        output = gsum.__repr__()
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'f73293da4f5d64545ad4a1d5a1efb283')

    def test_garmin_file_report_txt(self):
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gr = garmin_report.GarminReport()
        output = gr.file_report_txt(gfile)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '0929c060b23cb192f706d6964ffd75d6')
        
    def test_garmin_file_report_html(self):
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gr = garmin_report.GarminReport()
        script_path = CURDIR
        options = {'script_path': script_path}
        html_path = gr.file_report_html(gfile, copy_to_public_html=False, **options)
        file_md5 = [# ['altitude.png', '21175eae42854badcc793e1dc2e76258'],
                    # ['avg_speed_minpermi.png', '370eae2ada1e63bd24dd19352a8bbe7f'],
                    # ['avg_speed_mph.png', 'a6cb114e0a9e3f6eab20d0dcaf1d87e5'],
                    # ['heart_rate.png', 'b57ef5bb85895b295502ac9c0ba9ffac'],
                    # ['index.html', '8d1e6904cc1f375a3366f9efe6237afd'],
                    # ['mile_splits.png', '367951ddf6b5c7e221bc6056feeb3703'],
                    # ['speed_minpermi.png', 'd46baa636523321781975d24c51ea1c4'],
                    # ['speed_mph.png', 'ca248a6119d8886136023c4e5efe8935'],
                    ['index.html', '3d4ef3b462266754e4ab00d9cd7a53bc']]
        for f, fmd5 in file_md5:
            md5 = garmin_utils.get_md5('%s/%s' % (html_path, f))
            self.assertEqual(md5, fmd5)

    def test_garmin_total_summary_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.total_summary_report_txt(gsum, sport='running')
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '9f5aa437a6e8bbe6ecd25a088b634018')
        
    def test_garmin_day_summary_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.day_summary_report_txt(gsum, sport='running', cur_date=gsum.begin_datetime.date())
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'b05ddcddc03a64b650a75ad397037d00')

    def test_garmin_day_average_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.day_average_report_txt(gsum, sport='running', number_days=1)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '59c50d1eff34a78619e9f37e45445535')

    def test_garmin_week_summary_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        ic = gsum.begin_datetime.isocalendar()
        output = gr.week_summary_report_txt(gsum, sport='running',
                                            isoyear=ic[0], isoweek=ic[1], 
                                            number_in_week=1, 
                                            date=gsum.begin_datetime)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'e538e1b1abd954083c9cc19e14d04315')

    def test_garmin_week_average_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.week_average_report_txt(gsum, sport='running', number_of_weeks=1)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '4b649d4c617128138a1540c9dc2e1a09')

    def test_garmin_month_summary_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.month_summary_report_txt(gsum, sport='running',
                                             year=gsum.begin_datetime.year,
                                             month=gsum.begin_datetime.month,
                                             number_in_month=1)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'd2a1204e0374c7e83c450a1ae4ce3981')

    def test_garmin_month_average_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        output = gr.month_average_report_txt(gsum, sport='running', number_of_months=1)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '08a90d3c2e16ba2aafb4403e3ed69824')

    def test_garmin_year_summary_report_txt(self):
        gsum = garmin_summary.GarminSummary(FITFILE)
        gsum.read_file()
        gr = garmin_report.GarminReport()
        d = gsum.begin_datetime
        output = gr.year_summary_report_txt(gsum, sport='running',
                                            year=d.year, number_in_year=1)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'b7ab537ea3090fc44276b15bc61577b5')
        
    def test_garmin_cache_get_summary_list(self):
        gc = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR, cache_directory='%s/run/cache' % CURDIR)
        sl = gc.get_cache_summary_list(directory='%s/tests' % CURDIR)
        output = ('\n'.join('%s' % s for s in sorted(sl, key=lambda x: x.filename))).replace('ubuntu', 'ddboline').replace('/root', '/home/ddboline/setup_files/build')
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'bb7da3b34b92ed8b63b4359e265dd3f9')

    def test_cached_gfile(self):
        gc = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR, cache_directory='%s/run/cache' % CURDIR)
        gsum = garmin_summary.GarminSummary(FITFILE)
        gfile = gsum.read_file()
        test1 = '%s' % gfile
        gfname = os.path.basename(gfile.orig_filename)
        gc.write_cached_gfile(gfile)
        gfile_new = gc.read_cached_gfile(gfname)
        test2 = '%s' % gfile_new
        self.assertEqual(test1, test2)

    def test_summary_report(self):
        gc = garmin_cache.GarminCache(pickle_file='%s/temp.pkl.gz' % CURDIR, cache_directory='%s/run/cache' % CURDIR)
        sl = gc.get_cache_summary_list(directory='%s/tests' % CURDIR)
        rp = garmin_report.GarminReport(cache_obj=gc)
        options = {'do_plot': False, 'do_year': False, 'do_month': False, 'do_week': False, 'do_day': False, 'do_file': False, 'do_sport': None, 'do_update': False, 'do_average': False}
        script_path = CURDIR
        options['script_path'] = script_path
        output = rp.summary_report(sl, copy_to_public_html=False, **options)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), '022c8b604d32c9297195ad80aef5b73c')

if __name__ == '__main__':
    unittest.main()
