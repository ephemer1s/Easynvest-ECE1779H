
try:
    from flask import Flask
except:
    pass
import datetime

global memcache
global memcacheStatistics
global memcacheConfig

webapp = Flask(__name__)

# Memcache storage
memcache = {}

# memcache configurations: capacity in Bytes, policy 'LRU' or 'Random'
memcacheConfig = {'capacity': 10000000,  # 10 MB
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


# initialize Memcache stats
memcacheStatistics = Stats()

try:
    from backEnd import memcacheBackend
except:
    pass
