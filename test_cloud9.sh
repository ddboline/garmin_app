#!/bin/bash

nosetests --with-coverage --cover-package=garmin_app ./tests/garmin_app_unittests.py garmin_app/*.py

./garmin.py get
./garmin.py year run
./garmin.py 2014-11-22_18
