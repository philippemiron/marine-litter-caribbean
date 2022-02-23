from datetime import timedelta
from os.path import join

# folders
folder_current = '[path ocean velocity]'
folder_wind = '[path surface wind velocity]'
folder_output = '[basepath]/caribbean_marine_litter/data/output'
folder_release = '[basepath]/caribbean_marine_litter/data/process/release_locations'
files_release = [join(folder_release, 'file1.csv'), join(folder_release, 'file2.csv')]
file_unbeach = '[path to vector fields use for unbeaching]'

# temporal settings
dt = timedelta(hours=1)
output_freq = timedelta(hours=24)
repeat_release = None
kh = 1 # [m^2/s]
k_wind = 0.01 # windage factor i.e. U = k_wind * U0
