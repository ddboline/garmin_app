#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    Main module
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import garmin_app
from garmin_app.garmin_utils import garmin_arg_parse

if __name__ == '__main__':
    garmin_arg_parse(script_path=garmin_app.__path__[0])
