from flask import Flask

import datetime

global memcache
global memcacheStatistics
global memcacheConfig

webapp = Flask(__name__)

# Memcache storage
memcache = {}

# memcache configurations: capacity in Bytes, policy 'LRU' or 'Random'
memcacheConfig = {'capacity': 400000,  # 0.4 MB
                  'policy': 'LRU'}

# initilize memcache statistics


class Stat:
    """A Stat object has 2 members: 
        self.timestamp = Time when action is performed
        self.action = cache miss or cache hit
    """

    def __init__(self, _timestamp, _action):
        self.timestamp = _timestamp
        self.action = _action

# We seem to only need the stats within 10 mins so should also include timestamp?


class Stats:
    """The Stats class stores all the members and member function of the memcache statistics 

    public:
        self.list stores Stat objects, which includes timestamp and action (hit/miss)
        self.totalSize: (in Bytes) Size of files memcache currently stores
        self.numOfRequestsServed: Number of Requests Served

    """

    def __init__(self):
        self.list = []
        self.totalSize = 0
        self.numOfRequestsServed = 0
        self.index = -1

    def addStat(self, _stat):
        """Add a Stat object to self.list.

        Args:
            _stat (Stat): The Stat object being appended to the self.list
        """
        self.list.append(_stat)

    def getTenMinStats(self):
        """Get stats info within the previous 10 minutes. 
        Takes all the stats and filter the ones within 10 minutes,
        Calculate hitRate and missrate.

        Returns:
            tuple: (hitRate, missRate)
        """
        total = 0
        miss = 0
        hit = 0

        currentTime = datetime.datetime.now()
        tenMinAgo = currentTime - datetime.timedelta(minutes=10)  # 10 minutes

        for stat in self.list:
            if currentTime >= stat.timestamp and tenMinAgo <= stat.timestamp:
                if stat.action == "miss":
                    miss = miss+1
                    total = total + 1
                if stat.action == "hit":
                    hit = hit+1
                    total = total + 1

        if total == 0:
            return(0.0, 0.0)

        hitRate = hit/total
        missRate = miss/total

        return (hitRate, missRate)

    def getOneMinStats(self):
        """Get stats info within the previous 1 minutes. 
        Takes all the stats and filter the ones within 1 minutes,
        Calculate hitRate and missrate.

        Returns:
            missRate, hitRate, len(self.list), len(memcache), self.totalSize, total, timestamp
        """

        total = 0
        miss = 0
        hit = 0

        currentTime = datetime.datetime.now()
        oneMinAgo = currentTime - datetime.timedelta(minutes=1)  # 1 minutes

        for stat in self.list:
            if currentTime >= stat.timestamp and oneMinAgo <= stat.timestamp:
                if stat.action == "miss":
                    miss = miss + 1
                    total = total + 1
                if stat.action == "hit":
                    hit = hit + 1
                    total = total + 1

        if total == 0:
            return self.index, 0.0, 0.0, len(self.list), len(memcache), self.totalSize, total, currentTime.strftime("%Y-%m-%d %H:%M:%S")

        hitRate = hit/total
        missRate = miss/total

        return self.index, missRate, hitRate, len(self.list), len(memcache), self.totalSize, total, currentTime.strftime("%Y-%m-%d %H:%M:%S")

    def get5SecStats(self):
        """Get stats info within the previous 5Secs. 
        Takes all the stats and filter the ones within 5Secs,
        Calculate hitRate and missrate.

        Returns:
            missRate, hitRate, len(self.list), self.totalSize, total, timestamp
        """

        total = 0
        miss = 0
        hit = 0

        currentTime = datetime.datetime.now()
        # 5 Seconds!!!!!!!!!!!!!
        oneMinAgo = currentTime - datetime.timedelta(seconds=5)

        for stat in self.list:
            if currentTime >= stat.timestamp and oneMinAgo <= stat.timestamp:
                if stat.action == "miss":
                    miss = miss + 1
                    total = total + 1
                if stat.action == "hit":
                    hit = hit + 1
                    total = total + 1

        if total == 0:
            return self.index, 0.0, 0.0, len(self.list), self.totalSize, total, currentTime.strftime("%Y-%m-%d %H:%M:%S")

        hitRate = hit / total
        missRate = miss / total

        return self.index, missRate, hitRate, len(self.list), self.totalSize, total, currentTime.strftime("%Y-%m-%d %H:%M:%S")


# initialize Memcache stats
memcacheStatistics = Stats()


try:
    from backEnd import main
except Exception as e:
    print("wtf no Back End?")
    print("Error: ", e)
