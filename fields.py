import glob
import calendar
import datetime
from parcels import FieldSet
from os.path import join

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
    
    y0 = start_date.year
    y1 = end_date.year
    assert(y0 >= 2010 and y0 <= 2021)
    assert(y1 >= 2010 and y1 <= 2021)
    
    # add full years
    filenames = []
    for year in range(y0, y1+1):
        filenames.extend(glob.glob(join(base_folder, f'{year}', 'hycom_GLBv0.08_*.nc')))
    filenames = sorted(filenames)
    
    # trim before and after the time period
    i0 = [i for i, f in enumerate(filenames) if start_date.strftime("%Y%m%d") in f][0]
    i1 = [i for i, f in enumerate(filenames) if end_date.strftime("%Y%m%d") in f][-1]
    filenames = filenames[i0-1:i1+1]
    
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
    
    # TODO: switch to regional model and remove
    # for now we subset GLBv0.08 inside the Caribbean
    indices = {
        'lat': range(1500, 1894), # 0.0ºN, 31.52ºN
        'lon': range(1012, 1615), # 99.04ºW, -51.12ºW 1611
    }
    
    # chunksize: 128 to 512 are typically most effective (from parcel doc)
    cs = {'time': ('time', 1), 'lat': ('latitude', 512), 'lon': ('longitude', 512)}
    
    fset = FieldSet.from_netcdf(filenames, 
                                variables, 
                                dimensions, 
                                indices=indices,
                                deferred_load=True,
                                chunksize=cs,
                                allow_time_extrapolation=False)
    
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
    
    y0 = start_date.year
    y1 = end_date.year
    assert(y0 >= 2010 and y0 <= 2021)
    assert(y1 >= 2010 and y1 <= 2021)
    
    # add full years
    filenames = []
    for year in range(y0, y1+1):
        filenames.extend(glob.glob(join(base_folder, f'{year}w', 'JRA55_GLBv0.08_*.nc')))
    filenames = sorted(filenames)
    
    # trim before and after the time period
    i0 = [i for i, f in enumerate(filenames) if start_date.strftime("%Y%m%d") in f][0]
    i1 = [i for i, f in enumerate(filenames) if end_date.strftime("%Y%m%d") in f][-1]
    filenames = filenames[i0:i1+1]
    
    if len(filenames) == 0:
        raise Exception("Error: No HYCOM current file found.")

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
    
    # TODO: switch to regional wind model and remove
    # for now we subset JRA55_GLBv0.08 inside the Caribbean
    indices = {
        'lat': range(1500, 1889), # 0.0ºN, 31.0ºN
        'lon': range(1012, 1616), # 99.0ºW, 50.8ºW
    }
    
    # chunksize: 128 to 512 are typically most effective (from parcel doc)
    cs = {'time': ('time', 1), 'lat': ('latitude', 512), 'lon': ('longitude', 512)}
    
    fset = FieldSet.from_netcdf(filenames, 
                                variables, 
                                dimensions, 
                                indices=indices,
                                deferred_load=True,
                                chunksize=cs,
                                allow_time_extrapolation=False)
    
    if k_wind:
        fset.U.set_scaling_factor(k_wind)
        fset.V.set_scaling_factor(k_wind)
        
    return fset


def diffusion_field(fset, lat, lon, kh):
    """
    Adds constant diffusion coefficient to the FieldSet
    
    Args:
        fset: OceanParcel FieldSet obj
        lat: latitude grid
        lon: longitude grid
        kh: diffusivity constant
    """
    kh_mer = Field('Kh_meridional', kh * np.ones((len(lat), len(lon)), dtype=np.float32),
                   lon=lon, lat=lat, allow_time_extrapolation=True,
                   fieldtype='Kh_meridional', mesh='spherical', field_chunksize=(2048,2048))
    kh_zonal = Field('Kh_zonal', kh * np.ones((len(lat), len(lon)), dtype=np.float32),
                     lon=lon, lat=lat, allow_time_extrapolation=True,
                     fieldtype='Kh_zonal', mesh='spherical', field_chunksize=(2048,2048))

    fset.add_field(kh_mer, 'Kh_meridional')
    fset.add_field(kh_zonal, 'Kh_zonal')


def unbeaching_field(fset, lat, lon, input_file):
    """
    Adds the unbeaching field to the field_set
    
    Args:
        fset: OceanParcel FieldSet obj
        lat: latitude grid
        lon: longitude grid
        input_file: file containing the unbreaching field
    """
    ds = Dataset(input_file, "r+", format="NETCDF4")

    unBeachU= Field('unBeachU', ds['unBeachU'][:,:],
                    lon=lon, lat=lat, allow_time_extrapolation=True,
                    fieldtype='Kh_meridional', mesh='spherical', field_chunksize=(2048,2048))
    unBeachV= Field('unBeachV', ds['unBeachV'][:,:],
                    lon=lon, lat=lat, allow_time_extrapolation=True,
                    fieldtype='Kh_zonal', mesh='spherical', field_chunksize=(2048,2048))

    fset.add_field(unBeachU, 'unBeachU')
    fset.add_field(unBeachV, 'unBeachV')