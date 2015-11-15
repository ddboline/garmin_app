# -*- coding: utf-8 -*-

"""
    write cache objects to sql database
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from sqlalchemy import (create_engine, Column, Integer, Float, DateTime,
                        ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from .util import OpenPostgreSQLsshTunnel, POSTGRESTRING
from .garmin_corrections import list_of_corrected_laps, save_corrections

Base = declarative_base()
metadata = Base.metadata


class GarminCorrectionsStarts(Base):
    """ ORM class for garmin_corrections_starts table """
    __tablename__ = 'garmin_corrections_starts'

    id = Column(Integer, primary_key=True, unique=True)
    start_time = Column(DateTime, unique=True)
    distance = Column(Float)
    duration = Column(Float)

    def __repr__(self):
        return 'GarminCorrectionsStarts<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in ('id', 'start_time',
                                                      'distance', 'duration'))


class GarminCorrectionsLaps(Base):
    """ ORM class for garmin_corrections_laps table """
    __tablename__ = 'garmin_corrections_laps'

    id = Column(Integer, primary_key=True, unique=True)
    start_time = Column(DateTime,
                        ForeignKey('garmin_corrections_starts.start_time'))
    lap_number = Column(Integer)
    distance = Column(Float)
    duration = Column(Float)

    start_time_rel = relationship('GarminCorrectionsStarts')

    def __repr__(self):
        return 'GarminCorrectionsLaps<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in ('start_time', 'distance',
                                                      'duration'))


class GarminCorrectionsSQL(object):
    """ cache in SQL database using sqlalchemy """
    def __init__(self, sql_string='', pickle_file='', cache_directory='',
                 corr_list=None, garmin_corrections_=None, summary_list=None):
        if garmin_corrections_ is not None:
            self.garmin_corrections_ = garmin_corrections_
        else:
            self.garmin_corrections_ = list_of_corrected_laps()
        self.sql_string = sql_string
        self.summary_list = {}
        if isinstance(summary_list, dict):
            self.summary_list = summary_list
        elif isinstance(summary_list, list):
            self.summary_list = {v.filename: v for v in summary_list}

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

        for row in session.query(GarminCorrectionsStarts).all():
            gsum = GarminCorrectionsStarts()
            for sl_ in DB_ENTRIES:
                setattr(gsum, sl_, getattr(row, sl_))
            self.summary_list[gsum.filename] = gsum
        session.close()
        return self.summary_list

    def write_sql_table(self, summary_list):
        """ serialize into database """
        session = sessionmaker(bind=self.engine)
        session = session()

        slists = []

        def convert_to_sql(sl_):
            """ ... """
            sld = {x: getattr(sl_, x) for x in DB_ENTRIES}
            return GarminSummaryTable(**sld)

        for fn_, sl_ in summary_list.items():
            if not isinstance(sl_, GarminSummary):
                print(type(sl_))
            assert isinstance(sl_, GarminSummary)
            fn_ = sl_.filename
            if fn_ in self.summary_list:
                sl0 = self.summary_list[fn_]
                if not all(getattr(sl_, x) == getattr(sl0, x)
                           for x in DB_ENTRIES):
                    obj = session.query(GarminSummaryTable)\
                                 .filter_by(filename=fn_).all()[0]
                    session.delete(obj)
                    slists.append(convert_to_sql(sl_))
            else:
                slists.append(convert_to_sql(sl_))

        session.add_all(slists)
        session.commit()
        session.close()

    def get_cache_summary_list(self, directory, options=None):
        """ redirect call """
        return self.garmin_corrections_.get_cache_summary_list(directory,
                                                        options=options)


def write_postgresql_table(summary_list, get_summary_list=False,
                           dbname='garmin_summary'):
    """ convenience function """
    with OpenPostgreSQLsshTunnel(port=5433) as pport:
        return _write_postgresql_table(summary_list,
                                       get_summary_list=get_summary_list,
                                       dbname=dbname, port=pport)


def _write_postgresql_table(summary_list, get_summary_list=False,
                            dbname='garmin_summary', port=5432):
    """ ... """
    from .garmin_cache_sql import GarminCacheSQL
    postgre_str = '%s:%d/%s' % (POSTGRESTRING, port, dbname)
    gc_ = GarminCacheSQL(sql_string=postgre_str)
    sl_ = gc_.read_sql_table()
    if not get_summary_list:
        gc_.write_sql_table(summary_list)
    return sl_
