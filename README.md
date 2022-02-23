# Caribbean marine litter project

This project is a continuation of the work presented in [frontiers in Marine Science](https://www.frontiersin.org/journals/marine-science#), Tracking Marine Litter With a Global
Ocean Model: *Where Does It Go?
Where Does It Come From?* Eric P. Chassignet, Xiaobiao Xu and Olmo Zavala-Romero, 2021, [(link)](https://doi.org/10.3389/fmars.2021.667591), adapted to the Caribbean region.

Note: this repository was developed for a specific project at the [Center for Ocean-Atmospheric Prediction Studies](https://www.coaps.fsu.edu/).

# Getting ready

Replicate and activate the environment:

```
conda env create -f parcels_mpi.yml
conda activate parcels_mpi
```

## Modify the configuration file (config.py) to your study.
- folder_current: path to the current data files
- folder_wind: path to the wind data files
- folder_output: path to the output folder
- folder_release: path to file(s) containing the initial release locations
- files_release: filenames containing initial release locations (merge applied to all files)
- file_unbeach: path to file containing vector field use to unbeach particle
- dt: timestep during advection
- output_freq: output frequency of trajectories
- repeat_release: control the particle reinjection period
- kh: diffusivity constant to include a diffusion field
- k_wind: windage factor, i.e. `Uw *= k_wind`, with `Uw` the wind velocity

## Release locations

The initial position of the particles is controlled by `[folder_release]/[files_release]`. Particle are currently release at the coast and river outlets at the locations specified by `data/process/coasts.csv` and `data/process/rivers.csv`, respectively.

Those files are generated from density map of mismanaged plastic waste from Lebreton, laurent; Andrady, Anthony, 2019, [link](https://doi.org/10.6084/m9.figshare.5900335.v3). See `notebooks/subset_global_release.ipynb` and folder `data/raw/` for more information.

## Adaptation of the input of the velocity fields

Currently, the project uses a subset of the 1/12º HYCOM Global simulation with the JRA55 wind data set. The reading of both fields is handled respectively by `def hycom_fieldset()` and `def jra55_fieldset()` in `field.py`.  The plan is to switch to a 1/32º HYCOM regional model.

# Execution
The model can be run in serial or in parallel using the MPI version of parcels. The main script `caribbean_model.py` has a very simple API that allows to easily script batch releases.

```
python caribbean_model.py args
mpirun -np XX python caribbean_model.py args
```

The arguments are the same:
```
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
```

## Example
```
mpirun -np XX python caribbean_model.py 2010-1-1:0 2010:1:20:0 True True False example_run.nc
```
would execute in parallel between 1–20 Jan 2010 with added wind and diffusion but without unbeaching, and save the output in the `example_run.nc` file.

# Output

A very basic notebook `notebooks/visualize_output.ipynb` is avialable to visualize the output.
