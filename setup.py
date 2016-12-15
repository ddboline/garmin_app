#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import (absolute_import, division, print_function)

from setuptools import setup

setup(
    name='garmin_app',
    version='0.0.7.0',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='garmin_app',
    long_description='Garmin App',
    license='MIT',
    install_requires=['numpy'],
    packages=['garmin_app'],
    package_dir={'garmin_app': 'garmin_app'},
    package_data={'garmin_app': ['templates/*.html']},
    entry_points={'console_scripts':
                  ['garmin-app = garmin_app.garmin_utils:main',
                   'strava-upload = garmin_app.strava_upload:strava_upload']}
)
