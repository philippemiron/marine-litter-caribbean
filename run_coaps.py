import subprocess
from os.path import join
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import xarray as xr
import numpy as np

#
# make sure you activate the proper environment before launching the script
# 

# parameters
use_mpi = True
nb_proc = 16
start_date = datetime(2010, 1, 1)
end_date = datetime(2022, 1, 1)
folder = 'data/output/'
name = 'twelve_years_winds_diffusion_2010_01'
winds = 'True'
diffusion = 'True'
unbeach = 'False'
restart_file = ''

assert (start_date.day == end_date.day)

i = 1  # can modified to restart in the middle of a run
batch_end = start_date + relativedelta(months=1)
while start_date < end_date:
    # use MPI if nb particles > nb proc
    if restart_file:
        with xr.open_dataset(join(folder, restart_file)) as df:
            if sum(np.isfinite(df.lon[:,-1].values)) < nb_proc:
                use_mpi = False
    
    cmd = f'mpirun -np {nb_proc} ' if use_mpi else ''
    cmd+= f'python caribbean_model.py ' \
          f'{start_date.strftime("%Y-%m-%d:%H")} ' \
          f'{batch_end.strftime("%Y-%m-%d:%H")} '\
          f'{winds} ' \
          f'{diffusion} ' \
          f'{unbeach} ' \
          f'{name}_{i:03d}'

    if restart_file:
        cmd += f' {join(folder, restart_file)}'

    print(cmd)
    subprocess.call(cmd, shell=True)
    restart_file = f'{name}_{i:03d}.nc'
    start_date = batch_end
    batch_end += relativedelta(months=1)
    i += 1
