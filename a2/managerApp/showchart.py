import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def generate_seaborn_png(data, figname):
    '''
    generate chart for input data
    data: 2D array (or dataframe), timestamp should be included
    '''
    # process data
    assert isinstance(data, np.ndarray)
    y = data[:, 0]
    t = data[:, 1]

    # draw plot
    fig = plt.figure()
    ax = fig.subplot(1, 1)
    sns.lineplot(x=t, y=y, ax=ax)

    # save figure
    s = './static/'
    if not os.path.isdir(s):
        os.mkdir('./static')
    savepath = s + figname
    return plt.savefig(savepath)


