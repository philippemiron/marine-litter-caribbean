import subprocess
from os.path import join
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import xarray as xr
import numpy as np

#
# make sure you activate the proper environment before launching the script
# 

def particles_left(file):
    try:
        with xr.open_dataset(file) as ds:
            return np.sum(np.isfinite(ds.lon[:,-1].values))
    except:
        return 0
    
# parameters
nb_proc = 16
use_mpi = True
# monthly releases of particles
batch_start = datetime(2010, 2, 1)  # starting date from batch_start to batch_end
batch_end = datetime(2012, 1, 1)
end_date = datetime(2022, 1, 1)  # end date is always end_date
folder = 'data/output/'  # output folder
name = f"cm_uniform_mpw_{batch_start.year}_{batch_start.month:02d}"  # filename
winds = 'True'  # include windage
diffusion = 'True'  # include diffusion
unbeach = 'False'  # include unbeach fields
restart_file = ''  # use a restart file

assert (batch_start.day == batch_end.day)
assert (batch_start.day == end_date.day)

while batch_start < batch_end:
    run_start = batch_start
    run_end = batch_start + relativedelta(months=1)
    nb_parts = nb_proc  # initialize so it uses mpi if set
    i = 1
    mpi = use_mpi
    while run_start < end_date and nb_parts:
        # test enough particles left for mpi
        if mpi and nb_parts < nb_proc:
            mpi = False
    
        cmd = f'mpirun -np {nb_proc} ' if mpi else ''
        cmd+= f'python caribbean_model.py ' \
              f'{run_start.strftime("%Y-%m-%d:%H")} ' \
              f'{run_end.strftime("%Y-%m-%d:%H")} '\
              f'{winds} ' \
              f'{diffusion} ' \
              f'{unbeach} ' \
              f'{name}_{i:03d}'

        if restart_file:
            cmd += f' {join(folder, restart_file)}'

        print(cmd)
        subprocess.call(cmd, shell=True)
        nb_parts = particles_left(join(folder, f'{name}_{i:03d}.nc'))
        restart_file = f'{name}_{i:03d}.nc' if nb_parts else ''
        run_start = run_end
        run_end = run_start + relativedelta(months=1)
        i += 1

    # start the next monthly release
    batch_start += relativedelta(months=1)
    name = f"cm_mpw_{batch_start.year}_{batch_start.month:02d}"

