import glob
from datetime import datetime
from parcels import FieldSet, Field
from os.path import join
import numpy as np
import xarray as xr


def temporal_range(t: [datetime], start_date: datetime, end_date: datetime):
    """
    Return index of files to read in only necessary fields for the time period.
    This function is necessary because some files are missing from the dataset, so we have to find the closest time
    step to the start_date and end_date of the simulation.

    Args:
        t (list[datetime]): date time associated with files
        start_date (datetime): start of time period
        end_date (datetime): end of the time period

    Returns:
        slice: parcels object that holds velocity data for particle integration
    """

    i0 = [i for i, t in enumerate(t) if t <= start_date]
    i1 = [i for i, t in enumerate(t) if t >= end_date]

    # get closest before start_date and after end_date
    try:
        i0 = i0[-1]
    except IndexError:
        i0 = 0

    try:
        i1 = i1[0]
    except IndexError:
        i1 = len(t)

    return slice(i0, i1 + 1)


def hycom_fieldset(base_folder: str, start_date: datetime, end_date: datetime) -> FieldSet:
    """ Retrieve list of files requires for the specified time period and construct 
    a fieldset for the ocean velocity
    
    Args:
        base_folder (str): 
        start_date (datetime): start of time period
        end_date (datetime): end of the time period
    
    Returns: 
        FieldSet: parcels object that holds velocity data for particle integration
    """
    assert (start_date >= datetime(2010, 1, 1))
    assert (end_date <= datetime(2022, 1, 1))

    # add full years
    filenames = []
    for year in range(start_date.year, end_date.year + 1):
        for h in range(0,24,3): # avoid reading filenames with hours > 21
            filenames.extend(glob.glob(join(base_folder, f'{year}', f'hycom_GLBv0.08_*_t0{h:02d}.nc')))
    filenames = sorted(filenames)

    # file format hycom_GLBv0.08_XXX_2021010112_t000.nc
    filenames_t = [datetime.strptime(f[-18:-3], '%Y%m%d12_t0%H') for f in filenames]
    filenames = filenames[temporal_range(filenames_t, start_date, end_date)]  # restrict to temporal range

    if len(filenames) == 0:
        raise Exception("Error: No HYCOM current file found.")

    # create FieldSet
    variables = {
        'U': 'surf_u',
        'V': 'surf_v',
    }
    dimensions = {
        'lat': 'latitude',
        'lon': 'longitude',
        'time': 'time',
    }

    # chunk size of 128 to 512 are typically most effective (from parcel doc)
    cs = {'time': ('time', 1), 'lat': ('latitude', 128), 'lon': ('longitude', 128)}

    fset = FieldSet.from_netcdf(filenames,
                                variables,
                                dimensions,
                                #indices=indices,
                                deferred_load=True,
                                chunksize=cs,
                                allow_time_extrapolation=True)  # avoid issue when a file is missing

    return fset


def jra55_fieldset(base_folder: str, start_date: datetime, end_date: datetime, k_wind: float = 0.01) -> FieldSet:
    """ Retrieve list of files requires for the specified time period and construct fieldset
    for the surface wind velocity
    
    Args:
        base_folder (str): 
        start_date (datetime): start of time period
        end_date (datetime): end of the time period
    
    Returns: 
        FieldSet: parcels object that holds velocity data for particle integration
    
    """
    
    assert (start_date >= datetime(2010, 1, 1))
    assert (end_date <= datetime(2022, 1, 1))

    # add full years
    filenames = []
    for year in range(start_date.year, end_date.year + 1):
        for h in range(0,24,3): # avoid reading filenames with hours > 21
            filenames.extend(glob.glob(join(base_folder, f'{year}w', f'JRA55_GLBv0.08_*_t0{h:02d}.nc')))
    filenames = sorted(filenames)

    # file format JRA55_GLBv0.08_20210101_t000.nc
    filenames_t = [datetime.strptime(f[-16:-3], '%Y%m%d_T0%H') for f in filenames]
    filenames = filenames[temporal_range(filenames_t, start_date, end_date)]  # restrict to temporal range
    if len(filenames) == 0:
        raise Exception("Error: No JRA55 wind file found.")

    # create FieldSet
    variables = {
        'U': 'uwnd',
        'V': 'vwnd',
    }
    dimensions = {
        'lat': 'latitude',
        'lon': 'longitude',
        'time': 'time',
    }

    # chunksize: 128 to 512 are typically most effective (from parcel doc)
    cs = {'time': ('time', 1), 'lat': ('latitude', 128), 'lon': ('longitude', 128)}

    fset = FieldSet.from_netcdf(filenames,
                                variables,
                                dimensions,
                                #indices=indices,
                                deferred_load=True,
                                chunksize=cs,
                                allow_time_extrapolation=True)  # avoid issue when a file is missing

    fset.U.set_scaling_factor(k_wind)
    fset.V.set_scaling_factor(k_wind)

    return fset


def diffusion_field(fset: FieldSet, kh: float):
    """
    Adds constant diffusion coefficient to the FieldSet
    
    Args:
        fset: OceanParcel FieldSet obj
        kh (float): diffusivity constant
    """
    fset.add_constant_field("Kh_zonal", kh, mesh='spherical')
    fset.add_constant_field("Kh_meridional", kh, mesh='spherical')
    fset.add_constant("dres", 0.00005)


def unbeaching_field(fset: FieldSet, lat: np.array, lon: np.array, input_file):
    """
    Adds the unbeaching field to the field_set
    
    Args:
        fset: OceanParcel FieldSet obj
        lat (array): latitude grid
        lon (array): longitude grid
        input_file: netCDF file containing the velocity field used to unbeach particles
    """
    ds = xr.open_dataset(input_file)

    unBeachU = Field('unBeachU', ds['unBeachU'].values,
                     lon=lon,
                     lat=lat,
                     allow_time_extrapolation=True,
                     fieldtype='Kh_meridional',
                     mesh='spherical'
                     )
    unBeachV = Field('unBeachV', ds['unBeachV'].values,
                     lon=lon,
                     lat=lat,
                     allow_time_extrapolation=True,
                     fieldtype='Kh_zonal',
                     mesh='spherical'
                     )

    fset.add_field(unBeachU, 'unBeachU')
    fset.add_field(unBeachV, 'unBeachV')

    ds.close()
