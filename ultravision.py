import numpy as np
import pandas as pd
from pandas.io.common import EmptyDataError
import xarray as xr
import gc


# number of lines for the data header in ultravision text file export
NHEADER = 19


def _process_header(header, angles, fs, speed):
    out = dict(x=None, y=None, z=None, z_axis_type='time', units=None, focal_law=None)

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
    out['units'] = {'x': units['IndexResol'], 'y': units['ScanResol'], 'z': units['USoundResol']}

    # work on the time axis
    zstart = float(header['USoundStart'])
    if any(val is None for val in [angles, fs, speed]):
        print('Warning: scan parameters not specified. Falling back to header values for'
              'time axis, which might not be precise.')
        out['z'] = zstart + np.arange(nz) * float(header['USoundResol'])
        if 'Half Path' in ' '.join(parts[10]):
            out['z_axis_type'] = 'half path'
        elif 'True Depth' in ' '.join(parts[10]):
            out['z_axis_type'] = 'true depth'
        else:
            out['z_axis_type'] = 'unknown'
    else:
        # convert time to axis to time (seconds)
        if 'Half Path' in ' '.join(parts[10]):
            zstart *= 2/speed
        elif 'True Depth' in ' '.join(parts[10]):
            zstart *= 2/(speed*np.cos(np.deg2rad(angles[0])))
        else:
            # TODO: assuming True depth if nothing is specified
            zstart *= 2/(speed*np.cos(np.deg2rad(angles[0])))
        out['z'] = zstart + np.arange(nz)/fs
        out['units']['z'] = 's'

    out['focal_law'] = float(header['Focal Law'])
    return out


def _read_file(fname, angles=None, fs=None, speed=None):
    skiprows = 0
    headers, data = [], []
    n = 0
    only_first_header = False if any(val is None for val in [angles, fs, speed]) else True
    try:
        while True:
            if (only_first_header and (n == 0)) or (not only_first_header):
                # read header once. Ignore all other headers...
                header = pd.read_table(fname,
                                       skiprows=skiprows,
                                       nrows=NHEADER,
                                       sep='=',
                                       skipinitialspace=True,
                                       header=None,
                                       engine='c',
                                       index_col=0,
                                       squeeze=True).str.strip()
                headers.append(_process_header(header, angles, fs, speed))
            skiprows += NHEADER
            nx, ny, nz = len(headers[-1]['x']), len(headers[-1]['y']), len(headers[-1]['z'])
            u = pd.read_table(fname,
                              skiprows=skiprows,
                              nrows=nx * ny,
                              sep='\t',
                              skipinitialspace=True,
                              header=None,
                              engine='c',
                              index_col=False)
            # the last column is giving NaN values, just remove it.
            data.append(u.iloc[:, :-1].values.reshape(nx, ny, -1, order='F'))
            skiprows += nx * ny
            # memory management
            del u
            gc.collect()
            n += 1
    except EmptyDataError:
        # we reached end of file
        pass
    return headers, data


def read_ultravision(fname, angles=None, fs=None, speed=None):
    """
    Reads ultrasound scans saved in UltraVision (ZETEC, Inc. software) text file format.

    Parameters
    ----------
    fname : string
        The full path or relative path to the file.

    angles : float, array_like, optional
        The wave refracted angle in the test specimen. If the file contains phased array data
        (i.e. multiple angle), this can be a list of all the angles present in the file. Should
        have the same length as the number of angles exported in the file.

    fs : float, optional
        The time sampling frequency

    speed : float, optional
        The wave speed in the test specimen

    Returns
    -------
    : xarray.DataArray
        If (angles, fs, speed) are supplied, a 4-D datarray is returned if the files contains
        multiple angles, with the fourth dimension being the angle, otherwise if only one angle
        is present, a 3-D datarray is returned.

    : dict
        If any(angles, fs, speed) is not specified, then a dictionary is returned with each angle
        in the file as one data entry in the `dict`. We do this, because the time axis is not
        known if it is True Depth or Half Path. Thus it will be different for each angle,
        and we cannot put all of them in the same `DataArray`.
    """
    # convert angles to a list if it is not
    if angles is not None and not hasattr(angles, '__len__'):
        angles = [angles]

    headers, data = _read_file(fname, angles, fs, speed)

    # not phased array data
    if len(headers) == 1 and len(data) == 1:
        h, data = headers[0], data[0]
        out = xr.DataArray(data, coords=[('X', h['x']), ('Y', h['y']), ('Z', h['z'])])
    elif len(headers) == 1 and len(data) > 1:
        # Compute angle ID's if they are not specified
        h = headers[0]
        if angles is None:
            angles = np.arange(h['focal_law'], h['focal_law'] + len(data))
        out = xr.DataArray(np.stack(data, axis=3),
                           coords=[('X', h['x']),
                                   ('Y', h['y']),
                                   ('Z', h['z']),
                                   ('angle', angles)])
    else:
        if angles is None:
            angles = [h['focal_law'] for h in headers]
        out = {}
        for h, a, d in zip(headers, angles, data):
            out[a] = xr.DataArray(d, coords=[('X', h['x']), ('Y', h['y']), ('Z', h['z'])])
            out[a].coords['X'].attrs['units'] = h['units']['x']
            out[a].coords['Y'].attrs['units'] = h['units']['y']
            out[a].coords['Z'].attrs['units'] = h['units']['z']
            out[a].coords['Z'].attrs['projection'] = h['z_axis_type']

    if not isinstance(out, dict):
        out.coords['X'].attrs['units'] = headers[0]['units']['x']
        out.coords['Y'].attrs['units'] = headers[0]['units']['y']
        out.coords['Z'].attrs['units'] = headers[0]['units']['z']
        out.coords['Z'].attrs['projection'] = headers[0]['z_axis_type']

    return out
