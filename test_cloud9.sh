#!/bin/bash

./tests/garmin_app_unittests.py
./garmin.py get
./garmin.py sync
./garmin.py year run
./garmin.py 2014-11-22_18
