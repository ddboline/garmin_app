#!/bin/bash

if [ -d "/home/${USER}/.garmin_cache/run/gps_tracks" ]; then
    pass
else
    ./garmin.py get
fi

nosetests --with-coverage --cover-package=garmin_app ./tests/*.py garmin_app/*.py

# pyreverse garmin_app
# for N in classes packages; do dot -Tps ${N}*.dot > ${N}.ps ; ps2pdf ${N}.ps ; done
# ./garmin.py get
# ./garmin.py year run
# ./garmin.py 2014-11-22_18
