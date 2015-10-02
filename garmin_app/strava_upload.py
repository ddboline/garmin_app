#!/usr/bin/env python2
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import webbrowser
import os.path
import ConfigParser
import gzip
import argparse
import requests
from cStringIO import StringIO

from stravalib import Client, exc
from sys import stderr, stdin
from tempfile import NamedTemporaryFile

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


def strava_upload():
    """
        upload to strava, borrowed from https://github.com/dlenski/stravacli
    """
    allowed_exts = {'.tcx': lambda v: '<TrainingCenterDatabase' in v[:200],
                    '.gpx': lambda v: '<gpx' in v[:200],
                    '.fit': lambda v: v[8:12] == '.FIT'}

    par = argparse.ArgumentParser(description='Uploads activities to Strava.')
    par.add_argument('activities', nargs='*', type=argparse.FileType("rb"),
                     default=(stdin,),
                     help="Activity files to upload (plain or gzipped {})"
                          .format(', '.join(allowed_exts)))
    par.add_argument('-P', '--no-popup', action='store_true',
                     help="Don't browse to activities after upload.")
    par.add_argument('-E', '--env',
                     help='Look for ACCESS_TOKEN in environment variable '
                          'rather than ~/.stravacli')
    grp = par.add_argument_group('Activity file details')
    grp.add_argument('-p', '--private', action='store_true',
                     help='Make activities private')
    grp.add_argument('-t', '--type', choices=allowed_exts, default=None,
                     help='Force files to be interpreted as being of given '
                          'type (default is to autodetect based on name, or '
                          'contents for stdin)')
    grp.add_argument('-x', '--xml-desc', action='store_true',
                     help='Parse name/description fields from GPX and TCX '
                          'files.')
    grp.add_argument('-T', '--title', help='Activity title')
    grp.add_argument('-D', '--desc', dest='description',
                     help='Activity description')
    grp.add_argument('-A', '--activity-type', default=None,
                     help='Type of activity. If not specified, the default '
                          'value is taken from user profile. '
                          'Supported values: \n\t ride, run, swim, workout, '
                          'hike, walk, nordicski, alpineski, backcountryski, '
                          'iceskate, inlineskate, kitesurf, rollerski, '
                          'windsurf, workout, snowboard, snowshoe')
    args = par.parse_args()

    if args.xml_desc:
        if args.title:
            par.error('argument -T/--title not allowed with argument '
                      '-x/--xml-desc')
        if args.description:
            par.error('argument -D/--desc not allowed with argument '
                      '-x/--xml-desc')

    # Authorize Strava
    cid = 3163  # CLIENT_ID
    if args.env:
        cat = os.environ.get('ACCESS_TOKEN')
    else:
        cp_ = ConfigParser.ConfigParser()
        cp_.read(os.path.expanduser('~/.stravacli'))
        cat = None
        if cp_.has_section('API'):
            if 'access_token' in cp_.options('API'):
                cat = cp_.get('API', 'ACCESS_TOKEN')

    while True:
        client = Client(cat)
        try:
            athlete = client.get_athlete()
        except requests.exceptions.ConnectionError:
            par.error("Could not connect to Strava API")
        except Exception as e:
            print("NOT AUTHORIZED %s" % e, file=stderr)
            print("Need Strava API access token. Launching web browser to "
                  "obtain one.", file=stderr)
            client = Client()
            _uri = 'http://stravacli-dlenski.rhcloud.com/auth'
            _scope = 'view_private,write'
            authorize_url = client.authorization_url(client_id=cid,
                                                     redirect_uri=_uri,
                                                     scope=_scope)
            webbrowser.open_new_tab(authorize_url)
            client.access_token = cat = raw_input("Enter access token: ")
        else:
            if not cp_.has_section('API'):
                cp_.add_section('API')
            if not 'ACCESS_TOKEN' in cp_.options('API') \
                    or cp_.get('API', 'ACCESS_TOKEN', None) != cat:
                cp_.set('API', 'ACCESS_TOKEN', cat)
                cp_.write(open(os.path.expanduser('~/.stravacli'), "w"))
            break

    print("Authorized to access account of {} {} (id {:d})."
          .format(athlete.firstname, athlete.lastname, athlete.id))

    for act in args.activities:
        if act is stdin:
            contents = act.read()
            act = StringIO(contents)
            if args.type is None:
                # autodetect gzip and extension based on content
                if contents.startswith('\x1f\x8b'):
                    gz_, cf_, uf_ = '.gz', act, gzip.GzipFile(fileobj=act,
                                                              mode='rb')
                    contents = uf_.read()
                else:
                    gz_, uf_, cf_ = '', act, NamedTemporaryFile(suffix='.gz')
                    gzip.GzipFile(fileobj=cf_, mode='w+b').writelines(act)
                for ext, checker in allowed_exts.items():
                    if checker(contents):
                        print("Uploading {} activity from stdin..."
                              .format(ext+gz_))
                        break
                else:
                    par.error("Could not determine file type of stdin")
            else:
                base, ext = 'activity', args.type
        else:
            base, ext = os.path.splitext(act.name if args.type is None
                                         else 'activity.'+args.type)
            # autodetect based on extensions
            if ext.lower() == '.gz':
                base, ext = os.path.splitext(base)
                # un-gzip it in order to parse it
                gz_, cf_, uf_ = '.gz', act, None if args.no_parse else \
                                gzip.GzipFile(fileobj=act, mode='rb')
            else:
                gz_, uf_, cf_ = '', act, NamedTemporaryFile(suffix='.gz')
                gzip.GzipFile(fileobj=cf_, mode='w+b').writelines(act)
            if ext.lower() not in allowed_exts:
                par.error("Don't know how to handle extension "
                          "{} (allowed are {}).".format(ext,
                                                        ', '
                                                        .join(allowed_exts)))
            print("Uploading {} activity from {}...".format(ext+gz_, act.name))

        # try to parse activity name, description from file if requested
        if args.xml_desc:
            uf_.seek(0, 0)
            if ext.lower() == '.gpx':
                x = etree.parse(uf_)
                nametag, desctag = x.find("{*}name"), x.find("{*}desc")
                title = nametag and nametag.text
                desc = desctag and desctag.text
            elif ext.lower() == '.tcx':
                x = etree.parse(uf_)
                notestag = x.find("{*}Activities/{*}Activity/{*}Notes")
                if notestag is not None:
                    title, desc = (notestag.text.split('\n', 1) + [None])[:2]
        else:
            title = args.title
            desc = args.description

        # upload activity
        try:
            cf_.seek(0, 0)
            upstat = client.upload_activity(cf_, ext[1:] + '.gz', title, desc,
                                            private=args.private,
                                            activity_type=args.activity_type)
            activity = upstat.wait()
            duplicate = False
        except exc.ActivityUploadFailed as e:
            words = e.args[0].split()
            if words[-4:-1] == ['duplicate', 'of', 'activity']:
                activity = client.get_activity(words[-1])
                duplicate = True
            else:
                raise

        # show results
        uri = "http://strava.com/activities/{:d}".format(activity.id)
        print("  {}{}".format(uri, " (duplicate)" if duplicate else ''),
              file=stderr)
        if not args.no_popup:
            webbrowser.open_new_tab(uri)