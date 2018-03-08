"""
This script makes a short version of a typical data file exported from ultravision.
Note that the resulting file has been manually edited to fix the # of scan and index points in
the headers...
"""
from packages import utils
import pandas as pd
from os.path import join
from pandas.io.common import EmptyDataError

NHEADER = 19
NDATAKEEP = 10

conf = utils.get_configuration()['paths']['phase2']
fname = join(conf['data_dir'], 'paut_startup', 'experiment', 'halfpath_0skew.txt')

nskip = 0
lines_to_keep = []
# first get all header

try:
    while True:
        header = pd.read_table(fname,
                               skiprows=nskip,
                               nrows=NHEADER,
                               sep='=',
                               skipinitialspace=True,
                               header=None,
                               engine='c',
                               index_col=0,
                               squeeze=True)
        parts = header.index.str.split()
        # remove unit values from the header labels
        header.index = [' '.join([pi for pi in p if not any((c in pi) for c in set('[]()'))])
                        for p in parts]

        lines_to_keep += list(range(nskip, nskip + NHEADER + NDATAKEEP))
        nskip += int(header['ScanQty']) * int(header['IndexQty']) + NHEADER
        print(lines_to_keep)
except EmptyDataError:
    pass

# not open file and read line by line, selectively
with open(fname, 'r') as fid:
    content = fid.readlines()

with open('ultravision_example_pa.txt', 'w') as fid:
    fid.writelines([content[l] for l in lines_to_keep])