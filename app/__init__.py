from app import main
from flask import Flask
import os
import datetime

global d_memcache
global l_memcacheStatistics
global d_memcacheConfig

webapp = Flask(__name__)

# Memcache storage
d_memcache = {}
d_memcacheConfig = {}

# initilize memcache statistics


class Stat:

    def __init__(self, _timestamp, _action):
        self.timestamp = _timestamp
        self.action = _action

# We seem to only need the stats within 10 mins so should also include timestamp?


class Stats:

    def __init__(self):
        self.list = []

    def addStat(self, _stat):
        self.list.append(_stat)

    def getTenMinStats(self):

        total = 0
        miss = 0
        hit = 0

        currentTime = datetime.datetime.now()
        tenMinAgo = currentTime - datetime.timedelta(minutes=10)

        for stat in self.list:
            if currentTime >= stat.timestamp and tenMinAgo <= stat.timestamp:
                if stat.action == "miss":
                    miss = miss+1
                    total = total + 1
                if stat.action == "hit":
                    hit = hit+1
                    total = total + 1

        hitRate = hit/total
        missRate = miss/total

        return (hitRate, missRate)

# Memcache stats
l_memcacheStatistics = Stats()
