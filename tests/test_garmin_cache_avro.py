import gzip

from garmin_app import garmin_parse
from garmin_app import garmin_cache

GMNFILE = 'tests/test.gmn'
TCXFILE = 'tests/test.tcx'
FITFILE = 'tests/test.fit'
TXTFILE = 'tests/test.txt'
GPXFILE = 'tests/test.gpx'


def test():
    for fname in GMNFILE, TCXFILE, FITFILE, TXTFILE, GPXFILE:
        gfile = garmin_parse.GarminParse(fname)
        gfile.read_file()
        garmin_cache.write_garmin_file_object_to_file(gfile, 'test.avro')

        result = garmin_cache.read_avro_object('test.avro')

        assert gfile == result
