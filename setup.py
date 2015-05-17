#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals

from distutils.core import setup

setup(
    name='garmin_app',
    version='00.00.01',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='garmin_app',
    long_description='Garmin App',
    license='MIT',
#    install_requires=['pandas >= 0.13.0', 'numpy >= 1.8.0'],
    packages=['garmin_app'],
    package_dir={'garmin_app': 'garmin_app'},
    scripts=['bin/garmin.py']
)
