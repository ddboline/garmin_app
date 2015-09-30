#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals

from setuptools import setup

setup(
    name='garmin_app',
    version='00.00.01',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='garmin_app',
    long_description='Garmin App',
    license='MIT',
    test_suite = 'nose.collector',
    install_requires=['pandas', 'numpy', 'requests', 'sqlalchemy', 'pyusb'],
    packages=['garmin_app'],
    package_dir={'garmin_app': 'garmin_app'},
    package_data={'garmin_app': ['templates/*.html',
                                 'garmin_corrections.json']},
    entry_points={'console_scripts':
                    ['garmin-app = garmin_app.garmin_utils:main']}
)
