import subprocess
from os.path import join
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import xarray as xr
import numpy as np

# parameters
nb_proc = 16
mpi = True

# monthly releases of particles
start_date = datetime(2021, 10, 1)  # starting date
end_date = datetime(2022, 1, 1)  # end of the trajectories
folder = 'data/output/cm_mpw'  # output folder TODO: have to match config..
basename = 'cm_mpw'
winds = 'True'  # include windage
diffusion = 'True'  # include diffusion
unbeach = 'False'  # include unbeach fields
restart_file = ''  # use a restart file

assert (start_date.day == end_date.day)

name = f"{basename}_{start_date.strftime('%Y-%m-%d')}"  # filename
i = 1
run_start = start_date
run_end = run_start + relativedelta(months=1)
while run_start < end_date:
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
    restart_file = f'{name}_{i:03d}.nc'
    run_start = run_end
    run_end = run_start + relativedelta(months=1)
    i += 1

print('Combining and cleaning monthly files')
cmd = f"python run_tools.py {folder} {basename} {start_date.strftime('%Y-%m-%d')} True True"
print(cmd)
subprocess.call(cmd, shell=True)

