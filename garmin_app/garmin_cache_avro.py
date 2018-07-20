#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  8 10:27:15 2018

@author: ddboline
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)
import fastavro

from garmin_app.garmin_summary import GarminSummary
from garmin_app.garmin_file import GarminFile


def write_garmin_file_object_to_file(gfile, avro_file):
    parsed_schema = fastavro.parse_schema(GarminFile._avro_schema)
    js = [gfile.to_dict()]
    fastavro.writer(avro_file, parsed_schema, js, validator=True)


def read_avro_object(avro_file):
    parsed_schema = fastavro.parse_schema(GarminFile._avro_schema)
    for record in fastavro.reader(avro_file, parsed_schema):
        result = record
        break
    return GarminFile.from_dict(result)


class GarminCacheAvro(object):
    pass
