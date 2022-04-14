"""
Usage:
  run_tools.py <folder> <basename> <start_date> <combine> <clean>
  run_tools.py (-h | --help)
  run_tools.py --version

Options:
  -h --help      Show this screen
  --version      Show version
  <folder>       Folder
  <basename>     Filename prefix
  <start_date>   Start date with format %Y-%m-%d:%H
  <combine>      Combine monthly file [bool]
  <clean>        Clean monthly file [bool]
"""

from datetime import datetime
from os.path import isfile, join
import numpy as np
import xarray as xr
import glob
import os
from dateutil.relativedelta import relativedelta
from docopt import docopt
from distutils.util import strtobool
seconds_per_day = 60 * 60 * 24

def particles_left(file):
    try:
        with xr.open_dataset(file) as ds:
            return np.sum(np.isfinite(ds.lon[:,-1].values))
    except:
        return 0


def combine(folder, basename, start_date):
    name = f"{basename}_{start_date.strftime('%Y-%m-%d')}"
    files = sorted(glob.glob(join(folder, f'{name}_*.nc')))
    nb_traj = xr.open_dataset(files[0]).dims['traj']
    nb_obs = sum([xr.open_dataset(file).dims['obs'] for file in files]) - (len(files)-1)

    time = np.tile(np.arange(0, nb_obs, dtype='int16'), (nb_traj,1))  # manually daily output
    lon = np.full((nb_traj, nb_obs), np.nan)
    lat = np.full((nb_traj, nb_obs), np.nan)

    offset = 0
    for i, file in enumerate(files):
        df = xr.open_dataset(file, decode_times=False)

        # get trajectory id
        j = df.trajectory[:,0].values.astype('int')
        if i == 0:
            k = slice(offset, offset+df.dims['obs'])
            lon[j, k] = df.lon
            lat[j, k] = df.lat
            
            # Particle can be delayed on the first month but Parcels doesn't keep ds.time constant for
            # each particle. We realign (with np.roll) longitude and latitude to match time between particles.
            # Note: starting from the second month all particles are synchronized
            ptime = (df.time[:,0].values / seconds_per_day)
            ptime = (ptime - np.nanmin(ptime)).astype('int') # days
            pdelayed = ptime > 0  #  particles can start later in the first month
            lon[j[pdelayed], k] = np.array([np.roll(row, shift) for row,shift in zip(df.lon[pdelayed, :], ptime[pdelayed])])
            lat[j[pdelayed], k] = np.array([np.roll(row, shift) for row,shift in zip(df.lat[pdelayed, :], ptime[pdelayed])])
            offset += df.dims['obs']
        else:
            k = slice(offset, offset+df.dims['obs']-1)
            lon[j, k] = df.lon[:, 1:].values # initial position is repeated
            lat[j, k] = df.lat[:, 1:].values # initial position is repeated
            offset += df.dims['obs'] - 1
        df.close()
        
    # create and save yearly netCDF 
    xr.Dataset(
        data_vars=dict(
            # position and velocity
            lon=(['traj', 'obs'], lon, {'long_name': 'longitude', 'units':'degrees_east'}),
            lat=(['traj', 'obs'], lat, {'long_name': 'latitude', 'units':'degrees_north'}),
        ),

        coords=dict(
            time=(['traj', 'obs'], time, {'long_name': 'time', 'units': f'days since {start_date.strftime("%Y-%m-%d:%H")}'}),
        ),

        attrs={
            'title': 'Caribbean Marine Litter trajectories',
            'description': f'Particles released during {start_date.strftime("%Y-%m")}.',
            'institution': 'Florida State University Center for Ocean-Atmospheric Prediction Studies (COAPS)',
            'date_created': datetime.now().isoformat(),
        }
    ).to_netcdf(join(folder, f'{name}.nc'))

    start_date += relativedelta(months=1)


def clean(folder, basename, start_date):
    """
    If monthly archive was created, we clean the batch files
    """   
    name = f"{basename}_{start_date.strftime('%Y-%m-%d')}"
    
    if isfile(join(folder, f'{name}.nc')):
        files = sorted(glob.glob(join(folder, f'{name}_*.nc')))
        for file in files:
            os.remove(file)
    else:
        print('\tMonthly Archive was not previously created.')


# python run_tools.py args
if __name__ == "__main__":
    args = docopt(__doc__, version='0.1')

    # command line arguments
    folder = args['<folder>']
    basename = args['<basename>']
    start_date = datetime.strptime(args['<start_date>'], "%Y-%m-%d")
    do_combine = bool(strtobool(args['<combine>']))
    do_clean = bool(strtobool(args['<clean>']))

    print(f"\nCombining files")
    print(f"Parameters: {folder} {basename} {start_date} {do_combine} {do_clean}")

    if do_combine:
        combine(folder, basename, start_date)
    if do_clean:
        clean(folder, basename, start_date)
