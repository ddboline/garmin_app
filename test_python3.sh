#!/bin/bash

rm -rf run/
./garmin.py get
./garmin.py year run
./garmin.py 2014-11-22_18
./tests/garmin_app_unittests.py
