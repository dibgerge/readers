# Readers

Provides interfaces to read data exported from commonly used ultrasound simulation software and data acquisition hardware. There are four supported platforms: CIVA simulation exports, Ultravision, LeCroy Oscilloscope binary exports, and SAFT software binary exports.

## CIVA
 
Reads exported text simulation data files exported from CIVA. The functions available from the civa module:

#### `civa.cscan(file_name)`

Reads uncorrected C-Scan files.

**Returns**: `xarray.DataArray`. It has two coordinates `X` and `Y`, corresponding to the spatial scan directions. Each coordinate has an attribute `units`, accessed by `da.coords['X'].attrs['units']`, indicating the units of the coordinates.

#### `civa.true_cscan(file_name)`

Reads corrected C-Scan files.

**Returns**: `xarray.DataArray`. It has two coordinates `X` and `Y`, corresponding to the spatial scan directions. Each coordinate has an attribute `units`, accessed by `da.coords['X'].attrs['units']`, indicating the units of the coordinates.

#### `civa.bscan(file_name)`

Reads B-scan files. 

**Returns**: `xarray.DataArray`. It has two coordinates `X` and `Z`, corresponding to the spatial scan direction (`X`), and the wave propagation direction, or time axis (`Z`). Each coordinate has an attribute `units`, accessed by `da.coords['X'].attrs['units']`, indicating the units of the coordinates.

#### `civa.beam(file_name)`

Reads 2-D cross-sectional profiles of beam simulations.

**Returns**: `xarray.DataArray`. It has two coordinates `X` and `Z`, corresponding to the spatial direction (`X`), and the wave propagation direction - through thickness - (`Z`). Each coordinate has an attribute `units`, accessed by `da.coords['X'].attrs['units']`, indicating the units of the coordinates.

## LeCroy Oscilloscope Binaries

**`readers.lecroy(filename)`**
 
Reads standard binary files saved by the LeCroy oscilloscope. Returns a dictionary with the following fields:

- `info`: Information about the data acquisition, which was included in the header.
- `x`: An array of the horizontal values (usually time).
- `y`: An array of vertical values (usually volts).

## SAFT

**`readers.saft(fname)``**

Reads files saved by the SAFT software (proprietary). Currently a `pandas.Panel` (3-D array types) data type is returned, containing the three dimensions of an ultrasound scan: `items=Y`, `major_axis=t`, `minor_axis=X`.

## Ultravision

**``readers.ultravision(name, fs)``**

Reads exported text files from the Ultravision software by Zetec. Currently supports reading multiple measurements within the same file. 

**Inputs**

`fs` is the data acquisition sampling frequency in Hz. This is required because the header files in the exported file do not have accurate enough time axis (or depth) precision.


**Returns**

A `dict` of channels included in the file. The `keys` are the channel names, as specified in the header. Each entry in the dictionary is an `xarray` `DataArray`. It has three coordinates `X`, `Y`, and `Z`, corresponding to the spatial directions `X` and `Y`, and the time axis `Z`, computed based on the specified sampling frequency `fs`. Each coordinate has an attribute `units`, accessed by `da.coords['X'].attrs['units']`, indicating the units of the coordinates.
