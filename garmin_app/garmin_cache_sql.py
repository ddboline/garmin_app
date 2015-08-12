# -*- coding: utf-8 -*-

"""
    write cache objects to sql database
"""
from __future__ import print_function
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .garmin_cache import GarminCache
from .garmin_summary import GarminSummary

from sqlalchemy import (create_engine, Column, Integer, Float, String,
                        DateTime)
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class GarminSummaryTable(Base):
    __tablename__ = 'garmin_summary'

    filename = Column(String, primary_key=True)
    begin_datetime = Column(DateTime)
    sport = Column(String(12))
    total_calories = Column(Integer)
    total_distance = Column(Float)
    total_duration = Column(Float)
    total_hr_dur = Column(Integer)
    total_hr_dis = Column(Integer)
    number_of_items = Column(Integer)
    md5sum = Column(String(32))

    def __repr__(self):
        return 'GarminSummaryTable<%s>' % ', '.join(
            '%s=%s' % (x, getattr(self, x)) for x in GarminSummary.__slots__
            if x != 'corr_list')


class GarminCacheSQL:
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
        self.summary_list = summary_list if summary_list else []

        self.engine = create_engine(self.sql_string, echo=False)
        Base.metadata.create_all(self.engine)

    def delete_table(self):
        Base.metadata.drop_all(self.engine)

    def read_sql_table(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        for row in session.query(GarminSummaryTable).all():
            gsum = GarminSummary()
            for sl_ in gsum.__slots__:
                if sl_ != 'corr_list':
                    setattr(gsum, sl_, getattr(gsum, sl_))
            self.summary_list.append(gsum)
        session.close()
        return self.summary_list

    def write_sql_table(self, summary_list):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        slists = []
        for sl_ in summary_list:
            sld = {x: getattr(sl_, x) for x in sl_.__slots__
                   if x != 'corr_list'}
            slists.append(GarminSummaryTable(**sld))

        session.add_all(slists)
        session.commit()
        session.close()

    def get_cache_summary_list(self, directory, options=None):
        return self.garmin_cache.get_cache_summary_list(directory,
                                                        options=options)
