import numpy as np
import pandas as pd
from pandas.io.common import EmptyDataError
import xarray as xr
import gc


# number of lines for the data header in ultravision text file export
NHEADER = 19


def _process_header(header, fs):
    out = dict(channel=None, x=None, y=None, z=None, units=None)

    parts = header.index.str.split()
    # remove unit values from the header labels
    header.index = [' '.join([pi for pi in p if not any((c in pi) for c in set('[]()'))])
                    for p in parts]

    # construct the coordinates of the axes of the scan
    nx, ny, nz = int(header['ScanQty']), int(header['IndexQty']), int(header['USoundQty'])
    out['x'] = float(header['ScanStart']) + np.arange(nx) * float(header['ScanResol'])
    out['y'] = float(header['IndexStart']) + np.arange(ny) * float(header['IndexResol'])

    # get the units of the scan
    units = [p[-1][1:-1] if p[-1][0] == '(' and p[-1][-1] == ')' else None for p in parts]
    units = pd.Series(units, index=header.index)
    out['units'] = {'x': units['IndexResol'], 'y': units['ScanResol'], 'z': 'seconds'}
    out['z'] = np.arange(nz)/fs

    out['channel'] = header['Channel']
    return out


def ultravision(fname, fs):
    """
    Reads ultrasound scans saved in UltraVision (ZETEC, Inc. software) text file format.

    Parameters
    ----------
    fname : string
        The full path or relative path to the file.

    fs : float, optional
        The time sampling frequency. We use time starting from zero. If there is offset in data
        acquisition start time, it must be handled externally. We do not use the file header data
        for the time axis because it is inconsistent and imprecise.

    Returns
    -------
    : dict
        A dictionary is returned with each channel in the file as one data entry in the `dict`.
    """
    skiprows = 0
    out = {}
    try:
        while True:
            header = pd.read_table(fname,
                                   skiprows=skiprows,
                                   nrows=NHEADER,
                                   sep='=',
                                   skipinitialspace=True,
                                   header=None,
                                   engine='c',
                                   dtype=str,
                                   index_col=0,
                                   squeeze=True, memory_map=True)
            header = header.str.strip()
            header = _process_header(header, fs)
            skiprows += NHEADER
            nx, ny, nz = len(header['x']), len(header['y']), len(header['z'])
            u = pd.read_table(fname,
                              skiprows=skiprows,
                              nrows=nx * ny,
                              sep='\t',
                              skipinitialspace=True,
                              header=None,
                              engine='c',
                              index_col=False, memory_map=True)
            # the last column is giving NaN values, just remove it.
            u = u.iloc[:, :-1].values.reshape(nx, ny, -1, order='F')

            out[header['channel']] = xr.DataArray(u,
                                                  coords=[('X', header['x']),
                                                          ('Y', header['y']),
                                                          ('Z', header['z'])])
            skiprows += nx * ny
            # memory management
            del u
            gc.collect()
    except EmptyDataError:
        # we reached end of file
        pass
    return out
