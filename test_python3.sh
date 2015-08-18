#!/bin/bash

rm -rf run/
python3 ./garmin.py get
python3 ./garmin.py year run
python3 ./garmin.py 2014-11-22_18
python3 ./tests/garmin_app_unittests.py
