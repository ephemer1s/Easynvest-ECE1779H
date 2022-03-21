import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import time
import datetime as dt
import matplotlib
matplotlib.use('Agg')

# Data Example: [('2022-03-19 06:03', 0.15), ('2022-03-19 06:04', 0.29647), ('2022-03-19 06:05', 0.39)]


class Chart(object):
    x = None
    y = None
    style = {
        'missrate': {
            'title': 'Average Miss Rate',
            'ylim': (0, 100),
            'ylabel': 'percentage(%)',
        },
        'hitrate': {
            'title': 'Average Hit Rate',
            'ylim': (0, 100),
            'ylabel': 'percentage(%)',
        },
        'totalrequest': {
            'title': 'Total requests sent per minute',
            'ylim': None,
            'ylabel': 'requests',
        },
        'numofitems': {
            'title': 'total number of items in MemCache',
            'ylim': None,
            'ylabel': 'items',
        },
        'totalsize': {
            'title': 'total size of items in MemCache',
            'ylim': None,
            'ylabel': 'size (MB)',
        },
        'numofworkers': {
            'title': 'number of workers',
            'ylim': (0, 10),
            'ylabel': 'worker num',
        },
    }

    def __init__(self, name,
                 savepath='static/',
                 figsize=(20, 6),
                 ):
        '''
        Init the Chart object
        name: (str) choose from 'missrate' | 'hitrate' | 'totalrequest' | 'numofitems' | 'totalsize' | 'numofworkers'
        '''
        with sns.axes_style('darkgrid'):
            sns.set_context('poster')
            self.fig = plt.figure(figsize=figsize)  # init figure
            self.ax = self.fig.subplots(1, 1)

        if name in self.style:
            self.name = name
        else:
            raise Exception('Unsupported Metric Name: {}'.format(name))

        if not os.path.exists(savepath):  # Load save path
            if not os.path.isdir('./managerApp'):
                os.mkdir('managerApp')
            savepath = './managerApp/' + savepath
            if not os.path.isdir(savepath):
                os.mkdir(savepath)
        print('Drawing plot of {} using path {}'.format(name, savepath))
        self.savepath = savepath


    def timeascend(self, x, y):
        '''
        sort the data with time ascend.
        '''
        args = x.argsort()
        x = x[args]
        y = y[args]
        return x, y


    def ascend(self):
        '''
        sort the data with time ascend. return self.
        '''
        if self.x is not None and self.y is not None:
            args = self.x.argsort()
            self.x = self.x[args]
            self.y = self.y[args]
        return self


    # def percentage(self, y):
    #     '''
    #     make self.y percentile
    #     '''
    #     return y * 100


    def load(self, raw_data):
        '''
        Load and preprocess the data before drawing plot
        '''
        x, y = [], []
        for i in raw_data:
            if len(i) != 2:
                raise Exception(
                    'Raw data have less than 2 elements in one of its datapoints')
            else:
                x.append(i[0])
                y.append(i[1])
        x = [dt.datetime.strptime(t, '%Y-%m-%d %H:%M')
             for t in x if isinstance(t, str)]  # force transform str -> timestamp only if str
        self.x = np.array(x)
        self.y = np.array(y)
        if self.x is not None and self.y is not None:
            if self.name == 'missrate' or self.name == 'hitrate':
                self.y = self.y * 100
        
        return self


    def plot(self):
        '''
        Plot a lineplot and a scatterplot with input data.
        '''
        if self.x is not None and self.y is not None:
            # if self.name == 'missrate' or self.name == 'hitrate':   # re-implemented in self.load()
            #     self.y = self.y * 100
            sns.lineplot(x=self.x, y=self.y, ax=self.ax)
            sns.scatterplot(x=self.x, y=self.y, markers='.', ax=self.ax)

        else:
            raise Warning('Failed to plot: X and Y not loaded')

        self.ax.set(xlim=(self.x[-1] - dt.timedelta(minutes=30), self.x[-1]),
                    title=self.style[self.name]['title'],
                    ylabel=self.style[self.name]['ylabel'])

        if self.style[self.name]['ylim'] is not None:
            self.ax.set(ylim=self.style[self.name]['ylim'])
        else:
            self.ax.set(ylim=(0, float(max(self.y)) * 1.2))

        return self

    def save(self):
        '''
        Save figure drawed in self.fig
        '''
        path = self.savepath + self.name + '.png'

        self.fig.savefig(path)
        print('File saved at {}'.format(path))
        return self

    def close(self):
        '''
        Close figure instance, release resources
        '''
        plt.close(self.fig)
        return


# Usage:
if __name__ == '__main__':
    data = [('2022-03-19 06:03', 0.15), ('2022-03-19 06:04',
                                         0.29647), ('2022-03-19 06:05', 0.39)]
    Chart('missrate', figsize=(20, 6)).load(data).percentage().plot().save()
