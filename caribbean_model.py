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

from os.path import join
import pandas as pd
from docopt import docopt
from datetime import datetime, timedelta
from distutils.util import strtobool

from parcels import FieldSet, ParticleSet, ErrorCode, AdvectionRK4, DiffusionUniformKh
from particles import LitterParticle, coastal_particles, entering_particles
from kernels import *
from fields import hycom_fieldset, jra55_fieldset, diffusion_field, unbeaching_field
import config_uniform as config

try:
    from mpi4py import MPI
except ImportError:
    MPI = None
    print('MPI not found.')


def run(start_date, end_date, name='', winds=False, diffusion=False, unbeaching=False, restart_file=""):
    f_current = hycom_fieldset(config.folder_current, start_date, end_date)  # hycom ocean

    if winds:
        f_wind = jra55_fieldset(config.folder_wind, start_date, end_date, config.k_wind)  # jra55 wind
        main_fieldset = FieldSet(U=f_current.U + f_wind.U, V=f_current.V + f_wind.V)
    else:
        main_fieldset = FieldSet(U=f_current.U, V=f_current.V)

    # add diffusion or an unbeaching field to the main field
    if diffusion:
        diffusion_field(main_fieldset, config.kh)
    if unbeaching:
        unbeaching_field(main_fieldset, f_current.U.grid.lat, f_current.U.grid.lon, config.file_unbeach)

    # particles are set from initial locations or from the restart file
    if restart_file:
        print(f'Using restart file {restart_file}.')
        pset = ParticleSet.from_particlefile(fieldset=main_fieldset,  # advection field
                                             pclass=LitterParticle,  # custom marine litter particle
                                             filename=restart_file,  # assign (lat,lon) from ParticleFile
                                             repeatdt=config.repeat_release,  # reinjection (default: None)
                                             restart=True) 
        print(f"{pset.size} particles read from the restart file.", flush=True)

    else:
        df_coasts_rivers = coastal_particles(config, start_date)
        df_inputs = entering_particles(config, start_date)
        df = pd.concat([df_coasts_rivers, df_inputs], ignore_index=True, axis=0)

        pset = ParticleSet(fieldset=main_fieldset,  # advection field
                           pclass=LitterParticle,  # custom marine litter particle
                           lon=df.longitude,
                           lat=df.latitude,
                           time=df.date.values,
                           repeatdt=config.repeat_release)  # reinjection (default: None)
        print(f"{pset.size} particles ({len(df_coasts_rivers)} at coast & rivers, "
              f"{len(df_inputs)} at the boundaries) define for the monthly release.", flush=True)

    file_output = join(config.folder_output, f'{name}.nc')
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
            kernels += pset.Kernel(DiffusionUniformKh)

    run_time = timedelta(seconds=(end_date - start_date).total_seconds())

    pset.execute(kernels,  # the kernels (define how particles move)
                 endtime=end_date,  # end of the run
                 dt=config.dt,  # the time step of the kernel
                 recovery={ErrorCode.ErrorOutOfBounds: DeleteParticle},
                 output_file=outfile)

    print(f"Saving output to {file_output}.")
    outfile.export()  # to make sure the output file is generated

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
    print(
        f"Parameters: {start_date}->{end_date} winds={winds} diffusion={diffusion} "
        f"unbeaching={unbeaching} name={name} restart_file={restart_file}"
    )

    run(start_date, end_date, name, winds=winds, unbeaching=unbeaching, diffusion=diffusion, restart_file=restart_file)
