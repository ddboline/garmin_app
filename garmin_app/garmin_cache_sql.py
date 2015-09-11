# -*- coding: utf-8 -*-

"""
    write cache objects to sql database
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .garmin_cache import GarminCache
from .garmin_summary import GarminSummary, DB_ENTRIES
from sqlalchemy import (create_engine, Column, Integer, Float, String,
                        DateTime)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .util import OpenPostgreSQLsshTunnel, POSTGRESTRING

Base = declarative_base()

class GarminSummaryTable(Base):
    """ ORM class for garmin_summary table """
    __tablename__ = 'garmin_summary'

    filename = Column(String, primary_key=True)
    begin_datetime = Column(DateTime)
    sport = Column(String(12))
    total_calories = Column(Integer)
    total_distance = Column(Float)
    total_duration = Column(Float)
    total_hr_dur = Column(Float)
    total_hr_dis = Column(Float)
    number_of_items = Column(Integer)
    md5sum = Column(String(32))

    def __repr__(self):
        return 'GarminSummaryTable<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in DB_ENTRIES)


class GarminCacheSQL(object):
    """ cache in SQL database using sqlalchemy """
    def __init__(self, sql_string='', pickle_file='', cache_directory='',
                 corr_list=None, garmin_cache=None, summary_list=None):
        if garmin_cache is not None:
            self.garmin_cache = garmin_cache
        else:
            self.garmin_cache = GarminCache(pickle_file=pickle_file,
                             cache_directory=cache_directory,
                             corr_list=corr_list,
                             cache_read_fn=self.read_sql_table,
                             cache_write_fn=self.write_sql_table)
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
        Base.metadata.create_all(self.engine)

    def delete_table(self):
        """ drop table """
        Base.metadata.drop_all(self.engine)

    def read_sql_table(self):
        """ deserialize from database """
        session = sessionmaker(bind=self.engine)
        session = session()

        for row in session.query(GarminSummaryTable).all():
            gsum = GarminSummary()
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

        for sl_ in summary_list:
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
        return self.garmin_cache.get_cache_summary_list(directory,
                                                        options=options)


def write_postgresql_table(summary_list, get_summary_list=False):
    """ convenience function """
    with OpenPostgreSQLsshTunnel():
        from .garmin_cache_sql import GarminCacheSQL
        postgre_str = POSTGRESTRING + '/garmin_summary'
        gc_ = GarminCacheSQL(sql_string=postgre_str)
        sl_ = gc_.read_sql_table()
        if get_summary_list:
            return sl_
        gc_.write_sql_table(summary_list)
