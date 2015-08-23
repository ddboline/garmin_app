#!/bin/bash

nosetests ./tests/garmin_app_unittests.py garmin_app/*.py
rm -rf ${HOME}/run/
./garmin.py get
./garmin.py year run
./garmin.py 2014-11-22_18
