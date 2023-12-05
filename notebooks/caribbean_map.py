import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.feature as cfeature
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER

# 1-col and 2-col dimensions Frontier
width_fs = 7.086614173228347
width_hfs = 3.346456692913386
fs = (width_fs, 4.1)
fsh = (width_hfs, 1.936)

plt.rcParams.update(
    {
        'figure.constrained_layout.use': True, 
        'figure.autolayout': False,
        'text.usetex': False,
        'text.latex.preamble': '',
        'font.family': 'Latin Modern Math', # ['serif', 'sans-serif', 'cursive', 'fantasy', 'monospace']
        'font.style': 'normal',  # ['normal', 'italic', 'oblique']
        'font.weight': 'normal',  # ['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']
        'font.size': 7
    }
)

# other global settings
matplotlib.rcParams['xtick.major.pad'] = '1'
matplotlib.rcParams['ytick.major.pad'] = '1'
matplotlib.rcParams['xtick.labelsize'] = 6
matplotlib.rcParams['ytick.labelsize'] = 6

# projection of all plots
plot_crs = ccrs.PlateCarree()
data_crs = ccrs.PlateCarree()

# list of linestyles for bw plots
linestyles = ['-', '--', 'dotted', 'dashdot', (0, (3, 6))]

# colorbar ticks format
fmt_exp = matplotlib.ticker.ScalarFormatter(useMathText=True)
fmt_exp.set_powerlimits((0, 0))

# remove matplotlib depracation warning coming from cartopy geoaxis.py 
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap

def add_colorbar(fig, ax, var, fmt=None, range_limit=None):
    """Colorbar position and format properly"""
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.02, axes_class=plt.Axes)    
    cb = fig.colorbar(var, cax=cax, format=fmt)
    if range_limit:
        cb.mappable.set_clim(range_limit)    
    cb.ax.tick_params(which='major', labelsize=6, length=3, width=0.5, pad=0.05)
    return cb

def create_axis(fig, ni, nj, proj=None):
    axes = []
    k = 1
    for i in range(0, ni):
        for j in range(0, nj):
            if proj:
                axij = fig.add_subplot(ni, nj, k, projection=proj, aspect='equal')
            else:
                axij = fig.add_subplot(ni, nj, k, aspect='equal')
            axes.append(axij)
            k += 1
    return axes


def geo_map(ax, land=True):
    # ticks
    ax.set_xticks(np.arange(-95, -45, 10), crs=plot_crs)
    ax.set_yticks(np.arange(10, 40, 10), crs=plot_crs)
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())

    # add land and coastline
    if land:
        ax.add_feature(cfeature.LAND, facecolor='0.4', zorder=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=1)
    ax.set_extent([-98, -52, 4, 31], crs=plot_crs)
    

def filter_obj(tm, keep):
    """
    Restrict to a subset of elements
    """
    d = tm.domain
    tm.N = sum(keep)
    tm.P = tm.P[np.ix_(keep, keep)]
    tm.M = tm.M[keep]
    tm.B = tm.B[keep]
    d.bins = d.bins[keep, :]
    d.id_og = d.id_og[keep]
    if np.sum(tm.fi[keep] > 0):
        tm.fi = tm.fi[keep] / np.sum(tm.fi[keep])
    else:
        tm.fi = np.zeros(tm.N)
    tm.fo = 1 - np.sum(tm.P, 1)