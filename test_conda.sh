#!/bin/bash

if [ -d "/home/${USER}/.garmin_cache/run/gps_tracks" ]; then
    true
else
    python3 ./garmin.py get
fi

nosetests --with-coverage --cover-package=garmin_app ./tests/*.py garmin_app/*.py

# rm -rf ${HOME}/run/
# python3 ./garmin.py get
# python3 ./garmin.py year run
# python3 ./garmin.py 2014-11-22_18
