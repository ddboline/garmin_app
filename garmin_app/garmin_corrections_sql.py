# -*- coding: utf-8 -*-

"""
    write cache objects to sql database
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from sqlalchemy import (create_engine, Column, Integer, Float, DateTime, String)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from garmin_app.util import OpenPostgreSQLsshTunnel, POSTGRESTRING
from garmin_app.garmin_corrections import DB_ENTRIES, list_of_corrected_laps
from garmin_app.garmin_utils import print_date_string

Base = declarative_base()
metadata = Base.metadata


class GarminCorrectionsLaps(Base):
    """ ORM class for garmin_corrections_laps table """
    __tablename__ = 'garmin_corrections_laps'

    id = Column(Integer, primary_key=True, unique=True)
    start_time = Column(DateTime)
    lap_number = Column(Integer)
    distance = Column(Float)
    duration = Column(Float)
    unique_key = Column(String, unique=True)

    def __repr__(self):
        return 'GarminCorrectionsLaps<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in (
                'start_time', 'lap_number', 'distance', 'duration'))


class GarminCorrectionsSQL(object):
    """ cache in SQL database using sqlalchemy """
    def __init__(self, sql_string='', pickle_file='', cache_directory='',
                 corr_list=None, garmin_corrections_=None, summary_list=None):
        if garmin_corrections_ is not None:
            self.garmin_corrections_ = garmin_corrections_
        else:
            self.garmin_corrections_ = {}
        self.sql_string = sql_string

        self.engine = create_engine(self.sql_string, echo=False)
        self.create_table()

    def create_table(self):
        """ create table """
        metadata.create_all(self.engine)

    def delete_table(self):
        """ drop table """
        metadata.drop_all(self.engine)

    def read_sql_table(self):
        """ deserialize from database """
        session = sessionmaker(bind=self.engine)
        session = session()
        for row in session.query(GarminCorrectionsLaps).all():
            gsum = GarminCorrectionsLaps()
            for sl_ in DB_ENTRIES:
                setattr(gsum, sl_, getattr(row, sl_))
            key = print_date_string(gsum.start_time)
            lap = gsum.lap_number
            dur = gsum.duration
            dis = gsum.distance
            if key not in self.garmin_corrections_:
                self.garmin_corrections_[key] = {}
            if dur >= 0:
                self.garmin_corrections_[key][lap] = [dis, dur]
            else:
                self.garmin_corrections_[key][lap] = dis
        session.commit()
        session.close()
        return self.garmin_corrections_

    def write_sql_table(self, corrections):
        """ serialize into database """
        session = sessionmaker(bind=self.engine)
        session = session()

        slists = []

        id_ = 0
        q = session.query(GarminCorrectionsLaps).order_by(
            GarminCorrectionsLaps.id.desc()).first()
        if q:
            id_ += q.id + 1

        for st_, cor in corrections.items():
            for key, val in cor.items():
                if isinstance(val, list):
                    dis = val[0]
                    dur = val[1]
                else:
                    dis = val
                    dur = -1

                if st_ == 'DUMMY':
                    continue
                slists.append(GarminCorrectionsLaps(
                    id=id_, start_time=st_, lap_number=key, distance=dis,
                    duration=dur, unique_key='%s_%s' % (st_, key)))
                id_ += 1

        session.add_all(slists)
        session.commit()
        session.close()


def write_corrections_table(corrections, dbname='garmin_summary',
                            do_tunnel=False):
    """ convenience function """
    with OpenPostgreSQLsshTunnel(port=5433, do_tunnel=do_tunnel) as pport:
        return _write_corrections_table(corrections, dbname=dbname, port=pport)


def _write_corrections_table(corrections, dbname='garmin_summary', port=5432):
    """ ... """
    postgre_str = '%s:%d/%s' % (POSTGRESTRING, port, dbname)
    gc_ = GarminCorrectionsSQL(sql_string=postgre_str)
    sl_ = gc_.read_sql_table()
    gc_.delete_table()
    gc_.create_table()
    sl_.update(corrections)
    gc_.write_sql_table(corrections)
    return sl_


def read_corrections_table(dbname='garmin_summary', do_tunnel=False):
    with OpenPostgreSQLsshTunnel(port=5433, do_tunnel=do_tunnel) as pport:
        return _read_corrections_table(dbname=dbname, port=pport)


def _read_corrections_table(dbname='garmin_summary', port=5432):
    postgre_str = '%s:%d/%s' % (POSTGRESTRING, port, dbname)
    gc_ = GarminCorrectionsSQL(sql_string=postgre_str)
    return gc_.read_sql_table()


def test_garmin_corrections_sql():
    cor0 = list_of_corrected_laps()
    with OpenPostgreSQLsshTunnel(port=5433, do_tunnel=True) as pport:
        postgre_str = '%s:%d/%s' % (POSTGRESTRING, pport,
                                    'test_garmin_summary')
        gc_ = GarminCorrectionsSQL(sql_string=postgre_str)
        gc_.create_table()
        gc_.delete_table()
        gc_.create_table()
        gc_.write_sql_table(cor0)
        cor1 = gc_.read_sql_table()

        for key, val in cor0.items():
            if key == 'DUMMY':
                continue
            for lap in val:
                print(key, lap, cor0[key][lap], cor1[key][lap])
                if isinstance(val[lap], list):
                    assert abs(cor0[key][lap][0] - cor1[key][lap][0]) < 1e-6
                    assert abs(cor0[key][lap][1] - cor1[key][lap][1]) < 1e-6
                else:
                    assert abs(cor0[key][lap] - cor1[key][lap]) < 1e-6
