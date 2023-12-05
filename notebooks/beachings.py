import numpy as np
import xarray as xr
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

caribbean_countries = [  # countries
    "Antigua and Barbuda",
    "Bahamas",
    "Barbados",
    "Cuba",
    "Dominica",
    "Dominican Republic",
    "Grenada",
    "Haiti",
    "Jamaica",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Trinidad and Tobago",
    # dependant teritory
    "Anguilla",
    "Aruba",
    "Bonaire, Sint Eustatius and Saba",
    "British Virgin Islands",
    "Cayman Islands",
    "Curaçao",
    "Guadeloupe",
    "Martinique",
    "Montserrat",
    "Puerto Rico",
    "Saint-Barthélemy",
    "Saint-Martin",
    "Sint Maarten",
    "Turks and Caicos Islands",
    "Virgin Islands, U.S.",
    # other countries
    "Mexico",
    "United States",
    "Venezuela",
    "Belize",
    "Colombia",
    "Costa Rica",
    "Guatemala",
    "Guyana",
    "Honduras",
    "Nicaragua",
    "Panama",
    "Suriname",
]

global_c_list = pd.read_csv(
    "../data/raw/temp/country_reference_list.csv",
    header=None,
    index_col=0,
    names=["index", "country"],
)
map_cid = {}
for i, c in enumerate(caribbean_countries):
    map_cid[i] = global_c_list.loc[global_c_list["country"] == c].index[0]

# load country information
ds = xr.open_dataset("../data/process/country_GLBv0.08.nc")
closest_cid = ds.country.values
lon_cid = ds.plon.values
lat_cid = ds.plat.values
f_cid = RegularGridInterpolator((lon_cid, lat_cid), closest_cid.T, method="nearest")
ds.close()

# distance [km] from the coastlines (negative in the ocean)
# https://www.soest.hawaii.edu/pwessel/gshhg/
dist_coast = xr.open_dataset('../data/raw/dist_to_GSHHG_v2.3.7_1m.nc')

fdist = RegularGridInterpolator((dist_coast.lon.data, dist_coast.lat.data), 
                                 dist_coast.dist.data.T, bounds_error=False)

def global_country_id(lon, lat):
    caribbean_id = f_cid(np.column_stack((lon, lat))).astype("int")
    return [map_cid[i]-1 for i in caribbean_id]  # correct index for python


def decay(mass: float, age: float):
    """
    Calculate the mass decay of a plastic particles
    Args:
        mass: initial mass of the release plastic
        age: age of the particles [year]

    Returns:
        [float]: mass left in the ocean
    """
    # e-folding time from Chassignet, Xu, Zavala-Romero (2021)
    # 36.8% of plastic left after 5 years
    t0 = 5  # [years]
    return mass * np.exp(-age / t0)


def haversine(lon, lat):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    """
    lon, lat = map(np.radians, [lon, lat])

    dlon = lon[:, 1:] - lon[:, :-1]
    dlat = lat[:, 1:] - lat[:, :-1]

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, :-1]) * np.cos(lat[:, 1:]) * np.sin(dlon / 2.0) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))
    dist = 6371000 * c  # [m]
    return dist


def identify_beaching_c1(distance, eps, period):
    """
    From the traveled distance of a trajectory, find a beaching event, which is defined
    when a trajectory traveled less than a eps distance in a period of days

    Args:
        distance[array]: traveled distance per day [m]
        eps: distance minimal for a particle to be considered moving
        period: number of previous days where the distance is cummulated

    Return:
        id: index to the position/time where the trajectory is considered beached
    """
    idxf = np.argmax(np.isfinite(distance))  # first finite value
    if len(distance[idxf:]) > period:
        period_dist = np.sum(
            np.lib.stride_tricks.sliding_window_view(distance[idxf:], period), axis=1
        )
    else:
        period_dist = eps  # otherwise it would automatically beach at the end
    low_dist = period_dist < eps

    if np.all(~low_dist):
        return -99999
    else:
        return np.argmax(low_dist) + period + idxf


def identify_beaching_c2(distance, eps, period):
    """
    From a list of traveled distance of a trajectory, find beaching event, which is
    defined when a trajectory traveled distance is less than a minimal distance over a continous period of days.

    Args:
        distance[array]: traveled distance per day [m]
        eps: distance minimal for a particle to be considered moving
        period: number of continous days the criteria has to hold

    Return:
        id: index to the position/time where the trajectory is considered beached
    """

    low_dist = (distance < eps) * 1
    low_dist = np.insert(low_dist, [0, len(low_dist)], [0, 0])  # boundary conditions
    change_mvt = np.diff(low_dist)

    # find ranges of low displacement
    start = np.where(change_mvt == 1)[0]
    end = np.where(change_mvt == -1)[0]
    assert len(start) == len(end)
    length = end - start

    beachings = np.where(length >= period)[0]
    if len(beachings):
        return start[beachings[0]] + period  # first beaching criteria
    else:
        return -99999  # end of the release


def identify_beaching_c3(distance, probability, eps, delay):
    """
    
    Args:
        distance: distance from the shore (negative in the ocean)
        probability: prob to beach if particle closer than eps from shore
        eps: distance from shore where particles have prob to beach
        delay: only check if beached after delay days
    """
    
    # close from the shore
    close = distance > eps
    
    # probability of beaching
    beach = np.zeros_like(distance, dtype='bool')
    beach[close] = np.random.random_sample(size = np.sum(close)) < probability
    
    # remove probability of beaching for the first days
    beach[:,:delay] = 0
    
    # identify the first beaching
    beachings = np.argmax(beach, 1)
    beachings[beachings == 0] = -99999
    return beachings