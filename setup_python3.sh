#!/bin/bash

### hack...
export LANG="C.UTF-8"

sudo bash -c "echo deb ssh://ddboline@ddbolineathome.mooo.com/var/www/html/deb/trusty/python3/devel ./ > /etc/apt/sources.list.d/py2deb2.list"
sudo apt-get update
sudo apt-get install -y --force-yes gpsbabel garmin-forerunner-tools xml2 python3-requests \
                                    python3-pandas python3-dateutil python3-usb fit2tcx \
                                    python3-psycopg2 python3-sqlalchemy

if [ -z $1 ] ; then
    true
elif [ $1 = "html" ] ; then
    CURDIR=`pwd`
    cd ${HOME}
    git clone -b CLOUDVERSION https://github.com/ddboline/ddboline_html.git public_html
    cd public_html/
    sh setup_cloud9.sh
    mkdir garmin
    cd $CURDIR;
fi

### This is a bit of a hack...
if [ $USER = "ubuntu" ] ; then
    echo "America/New_York" > timezone
    sudo mv timezone /etc/timezone
    sudo rm /etc/localtime
    sudo ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime;
fi