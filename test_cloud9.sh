#!/bin/bash

./garmin.py get
./garmin.py sync
./garmin.py year run
./garmin.py 2014-11-22_18 plot
./unittests.py
./running_pace_plot.py
./world_record.py
