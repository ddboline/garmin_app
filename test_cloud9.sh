#!/bin/bash

if [ "$HOSTNAME" != "dilepton-tower" ]; then
    ssh -N -L localhost:5432:localhost:5432 ddboline@home.ddboline.net &
    sleep 5
fi

mkdir -p coverage
py.test --cov=garmin_app --cov-report html:coverage/ ./tests/*.py garmin_app/*.py

# pyreverse garmin_app
# for N in classes packages; do dot -Tps ${N}*.dot > ${N}.ps ; ps2pdf ${N}.ps ; done
# ./garmin.py get
# ./garmin.py year run
# ./garmin.py 2014-11-22_18
