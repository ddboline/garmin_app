#!/bin/bash

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools xml2
# sudo apt-get install -y python-mpltoolkits.basemap
sudo apt-get install -y python-pandas python-lockfile python-dateutil

if [ -z $1 ] ; then
    true
elif [ $1 == "html" ] ; then
    CURDIR=`pwd`
    cd ${HOME}
    git clone -b CLOUDVERSION https://github.com/ddboline/ddboline_html.git public_html
    cd public_html/
    sh setup_cloud9.sh
    mkdir garmin
    cd $CURDIR
fi
