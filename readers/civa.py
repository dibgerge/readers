import numpy as np
import xarray as xr
import pandas as pd
import re


def cscan(file_name):
    """
    Reads a C-scan file saved from a CIVA simulation. The X-Y axis coordinates are returned in
    units of meters.

    Parameters
    ----------
    file_name : string
        Full path name of the CIVA C-scan file.

    Returns
    -------
    cscan : xarray.DataArray
        The simulation C-scan. It has two coordinate axes: X, Y, and each coordinate has an
        attribute `units` indicating the units for the axis.
    """
    scan = pd.read_table(file_name,
                         sep=';',
                         usecols=[0, 1, 4],
                         encoding='iso8859_15',
                         index_col=[0, 1],
                         squeeze=True).unstack()
    da = xr.DataArray(scan.values, coords=[('Y', scan.index), ('X', scan.columns)])
    da.coords['X'].attrs['units'] = 'mm'
    da.coords['Y'].attrs['units'] = 'mm'
    return da


def true_cscan(file_name):
    """
    Reads a True C-scan file saved from a CIVA simulation.

    Parameters
    ----------
    file_name : str
        Full path name of the CIVA C-scan file

    Returns
    -------
    cscan : xarray.DataArray
        The simulation True C-scan. The `DataArray` has two coords: X, Y, and each coord has a
        `units` attribute.
    """
    with open(file_name) as fid:
        parts = fid.readline().split(';')
        xlims = [float(parts[1]), float(parts[2])]
        ylims = [float(parts[3]), float(parts[4])]

        # skip next line
        fid.readline()
        xstep = float(fid.readline().split(';')[1])
        ystep = float(fid.readline().split(';')[1])

    nx = int(np.round(np.diff(xlims)/xstep))
    ny = int(np.round(np.diff(ylims)/ystep))
    X = np.arange(nx)*xstep + xlims[0]
    Y = np.arange(ny)*ystep + ylims[0]

    data = np.genfromtxt(file_name,
                         delimiter=';',
                         skip_header=5,
                         usecols=(0, 1, 5))
    vals = np.zeros((len(Y), len(X)))
    x_ind = data[:, 1].astype(int)
    y_ind = data[:, 0].astype(int)
    vals[x_ind, y_ind] = data[:, 2]
    da = xr.DataArray(vals, coords=[('Y', Y), ('X', X)])
    da.coords['Y'].attrs['units'] = 'mm'
    da.coords['X'].attrs['units'] = 'mm'
    return da


def bscan(file_name):
    """
    Reads a B-scan txt file saved in CIVA-UT modeling software.

    Parameters
    ----------
    file_name : str
        Name of the file, including the full path if not in the current directory.

    Returns
    -------
    bscan : xarray.DatArray
        A `xarray.DataArray` object containing the B-scan.
    """
    # this is the default start of the header in a civa b-scan txt file
    skip_lines = 18

    # read the header
    with open(file_name) as fid:
        for i, line in enumerate(fid):
            if i == skip_lines-1:
                coords = re.findall(r'\d*\.?\d+', line)
                coords = np.array([float(val) for val in coords])
                cols = line.split(';')
                ind = np.array([j for j, c in enumerate(cols) if 'val' in c])
                break

    d = np.genfromtxt(file_name, delimiter=';', skip_header=skip_lines)
    # convert from microseconds in CIVA b-scan file to seconds
    Z = d[:, 0]*1e-6
    X = coords[ind-1]
    b = d[:, ind]

    da = xr.DataArray(b, coords=[('Z', Z), ('X', X)])
    da.coords['Z'].attrs['units'] = 's'
    da.coords['X'].attrs['units'] = 'mm'
    return da


def beam(file_name):
    """
    Reads a B-scan txt file saved in CIVA-UT modeling software.

    Parameters
    ----------
    file_name : str
        Name of the file, including the full path if not in the current directory.

    Returns
    -------
    bscan : xarray.DatArray
        A `xarray.DataArray` object containing the B-scan. The `DataArray` has two coords: X, Z
        and each coordinate has a `units` attribute.
    """
    # this is the default start of the header in a civa b-scan txt file
    skip_lines = 9

    with open(file_name) as fid:
        for i, line in enumerate(fid):
            if i == skip_lines-1:
                coords = re.findall(r'\d*\.?\d+', line)
                coords = np.array([float(val) for val in coords])
                cols = line.split(';')
                ind = np.array([j for j, c in enumerate(cols) if 'val' in c])
                break

    d = np.genfromtxt(file_name, delimiter=';', skip_header=skip_lines)
    # convert from microseconds in CIVA b-scan file to seconds
    Z = d[:, 0]
    X = coords[ind-1]
    b = d[:, ind]

    da = xr.DataArray(b, coords=[('Z', Z), ('X', X)])
    da.coords['Z'].attrs['units'] = 's'
    da.coords['X'].attrs['units'] = 'mm'
    return da
