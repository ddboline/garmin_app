import gzip

from garmin_app import garmin_parse
from garmin_app import garmin_cache_avro

GMNFILE = 'tests/test.gmn'
TCXFILE = 'tests/test.tcx'
FITFILE = 'tests/test.fit'
TXTFILE = 'tests/test.txt'
GPXFILE = 'tests/test.gpx'


def test():
    for fname in GMNFILE, TCXFILE, FITFILE, TXTFILE, GPXFILE:
        gfile = garmin_parse.GarminParse(fname)
        gfile.read_file()
        with gzip.open('test.avro.gz', 'wb') as f:
            garmin_cache_avro.write_garmin_file_object_to_file(gfile, f)
        
        with gzip.open('test.avro.gz', 'rb') as f:
            result = garmin_cache_avro.read_avro_object(f)
    
        assert gfile == result