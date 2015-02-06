#!/usr/bin/python
# -*- coding: utf-8 -*-

''' unittests... '''

import os
import unittest
import datetime
import dateutil.tz
import glob
import hashlib

GMNFILE = 'test/test.gmn'
TCXFILE = 'test/test.tcx'
FITFILE = 'test/test.fit'
TXTFILE = 'test/test.txt'

CURDIR = os.path.abspath(os.curdir)
print CURDIR
print '\n'.join(os.sys.path)

import garmin_app
import garmin_app.garmin_utils
import garmin_app.garmin_file
import garmin_app.garmin_parse
import garmin_app.garmin_cache
import garmin_app.garmin_report

try:
    from util import run_command, datetimefromstring
except ImportError:
    if os.path.exists('%s/scripts' % os.getenv('HOME')):
        os.sys.path.append('%s/scripts' % os.getenv('HOME'))
        from util import run_command, datetimefromstring

class TestGarminApp(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        #for f in glob.glob('temp.*.*.csv'):
            #if os.path.exists(f):
                #os.remove(f)
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
            #print gdf.to_html()
            md5 = run_command('cat temp.xml.lap.csv | md5sum', do_popen=True).read().split()[0]
            self.assertEqual(md5, 'dff5e558bced3ac4ca69927b6aed7858')

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
        #print gdf.describe()
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
        gcache = garmin_cache.GarminCache('temp.pkl.gz')
        gcache.write_pickle_object_to_file(gfile)
        del gfile

        gfile = gcache.read_pickle_object_in_file()
        gdf = garmin_cache.GarminDataFrame(garmin_file.GarminPoint, gfile.points).dataframe
        gdf.to_csv('temp.fit.point.csv', index=False)
        md5 = run_command('cat temp.fit.point.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '31a1ec7ed186440c28ff6ff052da13f3')

    def test_garmin_file_report_txt(self):
        gfile = garmin_parse.GarminParse(FITFILE)
        gfile.read_file()
        gr = garmin_report.GarminReport()
        output = gr.file_report_txt(gfile)
        m = hashlib.md5()
        m.update(output)
        self.assertEqual(m.hexdigest(), 'dc49eed73bf44c1b5d5c2444a59bec96')
        script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])
        options = {'script_path': script_path}
        gr.file_report_html(gfile, **options)

if __name__ == '__main__':
    unittest.main()
