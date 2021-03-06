#!/bin/bash

if [ "$HOSTNAME" != "dilepton-tower" ]; then
    ssh -N -L localhost:5432:localhost:5432 ddboline@home.ddboline.net &
    sleep 5
fi

mkdir -p coverage
py.test --cov=garmin_app --cov-report html:coverage/ ./tests/*.py garmin_app/*.py

# rm -rf ${HOME}/.garmin_cache/
# python3 ./garmin.py get
# python3 ./garmin.py year run
# python3 ./garmin.py 2014-11-22_18
