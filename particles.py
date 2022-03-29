from os.path import join
import numpy as np
import pandas as pd
from parcels import JITParticle
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class LitterParticle(JITParticle):
    """
    Littler Particle contains parameter to model the beaching and unbeaching process
    """
    # Empty for now
    # beached : 0 sea, 1 after RK, 2 after diffusion, 3 please unbeach, 4 final beached
    # beached = Variable('beached', dtype=np.int32, initial=0.)
    # beached_count = Variable('beached_count', dtype=np.int32, initial=0.)


def coastal_particles(config, start_date: datetime) -> pd.DataFrame:
    """
    Return initial locations of particles from the coasts and the rivers
        
    Args:
        config (obj): configuration parameters
        start_date (datetime): start of time period
    
    Returns: 
        df (DataFrame): dataset with particles data
    """

    # release locations from coasts and rivers   
    df = pd.concat([pd.read_csv(file) for file in config.files_release], ignore_index=True, axis=0)
    df['date'] = start_date  # release at the initial time
    columns = ['country id', 'longitude', 'latitude', 'date', 'weight [ton]']

    return df[columns]


def entering_particles(config, start_date: datetime) -> pd.DataFrame:
    """
    When a monthly releases is started this function includes the particles that will be entering the domain during
    the release month. Those entering particles are then advected together with the coastal and river particles until
    end of the simulation.

    Args:
        config (obj): configuration parameters
        name: name of the current run for output files
        start_date (datetime): start of time period
    
    Returns: 
        df (DataFrame): dataset with particles data
    """

    # input into the subregion from the start_date to the end of the month
    # assuming monthly releases
    assert (start_date.day == 1)  # start at the beginning of the month
    end_date = start_date + relativedelta(months=1) + timedelta(days=-1)  # end of the release month
    
    if config.files_boundary:
        df = pd.concat([pd.read_csv(file, parse_dates=['date']) for file in config.files_boundary], ignore_index=True,
                       axis=0)
        df = df.loc[np.logical_and(df['date'] >= start_date, df['date'] < end_date)]
        columns = ['country id', 'longitude', 'latitude', 'date', 'weight [ton]']

        return df[columns]
    else:
        None
