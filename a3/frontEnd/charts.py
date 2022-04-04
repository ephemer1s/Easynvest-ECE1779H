'''
charts.py --
Author : ephemer1s
Description : 
    tool functions for processing data and pass variables to chart.js, used in frontEnd/main.py
'''


from datetime import datetime
from dateutil import tz, relativedelta

import numpy as np


class Chart():

    def __init__(self):
        pass


    def to_timestamp(self, lst):
        '''
        convert a list of 3 integer to timestamp
        Input: 
         - lst: list[int], Year, Month, Day, example:[2022, 2, 22]
        '''
        return datetime(year=lst[0], month=lst[1], day=lst[2])


    def is_off(self, dt):
        '''
        decide whethen it is a day off or not
        '''
        # TODO: implementation here
        return False


    def get_latest_stamp(self, timestamp=None):
        '''
        get the last time that the stockexchange is active.
        will return now at 9:30 - 15:59 est & 15:59 at 16:00 - 9:29 est.
        Input:
         - timestamp: datetime.timestamp, use as input time, set to none to use current time, default = None
        Return: datetime.timestamp, the latest active minute of stockexchange.
        '''
        if timestamp is not None:  # range mode
            print('using given timestamp')
            now = timestamp
        else:
            now = datetime.now(tz=tz.gettz('America/New_York'))


        while self.is_off(now + relativedelta(days=-1)):
            # TODO: implement is_off(dt)
            now = now + relativedelta(days=-1)
            pass
        if self.is_off(now) or now.hour > 16:
            return now + relativedelta(
                hour=16, minute=0, second=0, microsecond=0)
        elif now.hour * 100 + now.minute < 930:
            return now + relativedelta(
                days=-1, hour=16, minute=0, second=0, microsecond=0)
        else:
            return now + relativedelta(microsecond=0)


    def generate_xlabels(self, daterange=None, dateperiod=60, interval=5):
        '''
        generate a series of xlabel for plotting chart in chart.js
        Input:
         - daterange: tuple of list[year, month, day], default = None
         - dateperiod: int, indicating total recent days to show, default = 1 (days)
         - interval: granularity of showing data, default = 5 (minutes)
        '''
        xlabels = []
        if daterange is None:
            to = self.get_latest_stamp()
            frm = to + relativedelta(days=-dateperiod)

        else:
            frm = self.to_timestamp(daterange[0])
            to = self.to_timestamp(daterange[1])
            if datetime.today() == to.date():
                to = self.get_latest_stamp()
            else:
                to = to + relativedelta(hour=16, minute=0, second=0, microsecond=0)

        return xlabels
