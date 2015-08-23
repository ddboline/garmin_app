#!/bin/bash

nosetests ./tests/garmin_app_unittests.py garmin_app/*.py
rm -rf ${HOME}/run/
python3 ./garmin.py get
python3 ./garmin.py year run
python3 ./garmin.py 2014-11-22_18
