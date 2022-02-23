"""
Usage:
  caribbean_model.py <start_date> <end_date> <winds> <diffusion> <unbeaching> <name> [<restart_file>]
  caribbean_model.py (-h | --help)
  caribbean_model.py --version

Options:
  -h --help      Show this screen.
  --version      Show version.
  <start_date>   Start date with format %Y-%m-%d:%H
  <end_date>     Start date with format %Y-%m-%d:%H
  <winds>        Includes winds [bool]
  <diffusion>    Includes diffusion [bool]
  <unbeaching>   Includes unbeaching field [bool]
  <name>         Name of the simulation use for filenames
  <restart_file> Start particles from last positions using ParticleFile
"""

import sys
import os
from os.path import join
import numpy as np
import functools
import pandas as pd
import time
from docopt import docopt
from datetime import datetime, timedelta
from distutils.util import strtobool

from parcels import FieldSet, JITParticle, ParticleSet, ErrorCode, AdvectionRK4
from particles import LitterParticle
from kernels import *
from fields import hycom_fieldset, jra55_fieldset, diffusion_field, unbeaching_field
import config

try:
    from mpi4py import MPI
except:
    MPI = None
    print('MPI not found.')

def run(start_date, end_date, name='', winds=False, diffusion=False, unbeaching=False, restart_file=""):
    
    # hycom ocean
    f_current = hycom_fieldset(config.folder_current, start_date, end_date)
    
    # jra55 wind
    if winds:
        f_wind = jra55_fieldset(config.folder_wind, start_date, end_date, config.k_wind)
        main_fieldset = FieldSet(U=f_current.U+f_wind.U, V=f_current.V+f_wind.V)
    else:
        main_fieldset = FieldSet(U=f_current.U, V=f_current.V)
    
    # add diffusion or an unbeaching field to the main field
    if diffusion:
        diffusion_field(main_fieldset, f_current.U.grid.lat, f_current.U.grid.lon, config.kh)
    if unbeaching:
        unbeaching_field(main_fieldset, f_current.U.grid.lat, f_current.U.grid.lon, config.file_unbeach)
    
    # particles are set from the restart_file or the initial release locations of mismanaged plastic waste
    if restart_file:
        print(f'Using restart file {restart_file}.')
        pset = ParticleSet.from_particlefile(fieldset=main_fieldset,  # advection field
                                             pclass=LitterParticle,   # custom marine litter particle
                                             filename=restart_file,   # assign (lat,lon) from ParticleFile
                                             repeatdt=config.repeat_release) # reinjection (default: None)
    else:
        # release locations from coasts and rivers
        lon0 = np.hstack([pd.read_csv(file).lon for file in config.files_release])
        lat0 = np.hstack([pd.read_csv(file).lat for file in config.files_release])
        w0   = np.hstack([pd.read_csv(file).weight for file in config.files_release])
        
        pset = ParticleSet(fieldset=main_fieldset,           # advection field
                           pclass=LitterParticle,            # custom marine litter particle
                           lon=lon0, lat=lat0,               # initial position
                           weight=w0,                        # weight assign to particle
                           repeatdt=config.repeat_release) # reinjection (default: None)
    
    file_output = join(config.folder_output, name)
    outfile = pset.ParticleFile(name=file_output, outputdt=config.output_freq)
    
    # combining kernels
    if unbeaching:
        kernels = pset.Kernel(AdvectionRK4Beached)
    else:
        kernels = pset.Kernel(AdvectionRK4)

    if unbeaching:
        kernels += pset.Kernel(BeachTesting_2D)
        kernels += pset.Kernel(UnBeaching)
        if diffusion:
            kernels += pset.Kernel(BrownianMotion2DUnbeaching)
            kernels += pset.Kernel(BeachTesting_2D)
    else:
        if diffusion:
            kernels += pset.Kernel(BrownianMotion2D)
    
    run_time = timedelta(seconds=(end_date - start_date).total_seconds())
    print(f"Running with {pset.size} particles for {run_time}.", flush=True)
    t = time.time()
        
    pset.execute(kernels,                  # the kernels (define how particles move)
                 runtime=run_time,         # the total length of the run
                 dt=config.dt,           # the timestep of the kernel
                 recovery={ErrorCode.ErrorOutOfBounds: DeleteParticle},
                 output_file=outfile)

    print(f"Done in time={time.time()-t:.1f} s.")
    print(f"Saving output to {file_output}.")
    outfile.export() # to make sure file is written

    if MPI:
        print(f"Waiting for file to be saved process {MPI.COMM_WORLD.Get_rank()}.", flush=True)
        MPI.COMM_WORLD.Barrier()

# Serial: python caribbean_model.py args
# Parallel: mpirun -np XX python caribbean_model.py args
if __name__ == "__main__":
    args = docopt(__doc__, version='0.2')   
    
    # command line arguments
    start_date = datetime.strptime(args['<start_date>'], "%Y-%m-%d:%H")
    end_date = datetime.strptime(args['<end_date>'], "%Y-%m-%d:%H")
    winds = bool(strtobool(args['<winds>']))
    diffusion = bool(strtobool(args['<diffusion>']))
    unbeaching = bool(strtobool(args['<unbeaching>']))
    name = args['<name>']
    restart_file = args['<restart_file>']
    
    print(f"\nMarine litter: Caribbean subregion")
    print(f"Parameters: {start_date}->{end_date} winds={winds} diffusion={diffusion} unbeaching={unbeaching} output_file={name} restart_file={restart_file}")

    run(start_date, end_date, name, winds=winds, unbeaching=unbeaching, diffusion=diffusion, restart_file=restart_file)