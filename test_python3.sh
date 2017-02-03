#!/bin/bash

py.test3 --with-coverage --cover-package=garmin_app ./tests/*.py garmin_app/*.py

# rm -rf ${HOME}/.garmin_cache/
# python3 ./garmin.py get
# python3 ./garmin.py year run
# python3 ./garmin.py 2014-11-22_18
