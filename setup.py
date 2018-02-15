#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import (absolute_import, division, print_function)
import sys
from setuptools import setup

console_scripts = (('garmin-app', 'garmin_app.garmin_utils:main'),
                   ('strava-upload', 'garmin_app.strava_upload:strava_upload'))

if sys.version_info.major == 2:
    console_scripts = ['%s = %s' % (x, y) for x, y in console_scripts]
else:
    v = sys.version_info.major
    console_scripts = ['%s%s = %s' % (x, v, y) for x, y in console_scripts]

setup(
    name='garmin_app',
    version='0.0.8.8',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='garmin_app',
    long_description='Garmin App',
    license='MIT',
    install_requires=['numpy'],
    packages=['garmin_app'],
    package_dir={'garmin_app': 'garmin_app'},
    package_data={'garmin_app': ['templates/*.html']},
    entry_points={
        'console_scripts': console_scripts
    })
