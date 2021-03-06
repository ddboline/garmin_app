#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013. Amazon Web Services, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    Save to AWS S3
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

# Import the SDK
import boto3
import os
import glob


def save_to_s3(bname='garmin_scripts_gps_files_ddboline', filelist=None):
    """
        function to save to s3, bname is bucket name
        filelist is list of files to add or overwrite
    """
    s3_ = boto3.resource('s3')
    bucket = s3_.create_bucket(Bucket=bname)
    list_of_keys = get_list_of_keys(bname=bname)
    if not filelist:
        filelist = []
    for fn_ in filelist:
        if not os.path.exists(fn_):
            print('file doesnt exists %s' % fn_)
            continue
        kn_ = fn_.split('/')[-1]
        with open(fn_, 'rb') as infile:
            if kn_ in list_of_keys:
                k = bucket.Object(kn_)
                if int(k.last_modified.strftime("%s")) > int(os.stat(fn_).st_mtime):
                    print(fn_, int(k.last_modified.strftime("%s")), int(os.stat(fn_).st_mtime))
                    continue
            else:
                k = bucket.Object(kn_)
                k.upload_fileobj(infile)
            list_of_keys[k.key] = k.e_tag.replace('"', '')
            print('upload to s3:', kn_, fn_, list_of_keys[k.key])
    return list_of_keys


def get_list_of_keys(bname='garmin_scripts_gps_files_ddboline'):
    """ get list of keys """
    s3_ = boto3.resource('s3')
    bucket = s3_.create_bucket(Bucket=bname)
    list_of_keys = {}
    for key in bucket.objects.all():
        list_of_keys[key.key] = key.e_tag.replace('"', '')
    return list_of_keys


def download_from_s3(bucket_name='garmin_scripts_gps_files_ddboline', key_name='', fname=''):
    """ download file """
    s3_ = boto3.resource('s3')
    if not key_name or not fname:
        return False
    dname = os.path.dirname(fname)
    if not os.path.exists(dname):
        os.makedirs(dname)
    bucket = s3_.create_bucket(Bucket=bucket_name)
    bucket.Object(key_name).download_file(fname)


if __name__ == '__main__':
    save_to_s3('garmin_scripts_gps_files_ddboline', glob.glob('gps_tracks/*'))
