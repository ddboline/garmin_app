#!/bin/bash

sudo cp -a ${HOME}/.ssh /root/
sudo chown -R root:root /root/
sudo bash -c "echo deb ssh://ddboline@home.ddboline.net/var/www/html/deb/xenial/devel ./ > /etc/apt/sources.list.d/py2deb2.list"
sudo apt-get update
sudo apt-get install -y --force-yes gpsbabel garmin-forerunner-tools xml2 python-requests \
                                    python-pandas python-dateutil python-usb fit2tcx \
                                    python-psycopg2 python-sqlalchemy python-pytest \
                                    python-pytest-cov python-numpy=1.\* libtinyxml2.6.2v5 \
                                    python-boto python-lxml python-matplotlib \
                                    python-stravalib python-setuptools python-dev \
                                    python-futures

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
