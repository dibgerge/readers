# Readers

Provides interfaces to read data exported from from commonly used software and hardware within the Applied Physics group. 

## CIVA readers
 
Reads simulation data files exported from CIVA. Types of files which can be read includes B-scans, C-scans, True C-scans, and cross-sections of beam simulations.

The returned data type for all read files is an `xarray` DataArray.

## LeCroy readers
 
This reads standard binary files saved by the LeCroy oscilloscope. Returns a dictionary with the following fields:

- `info`: Information about the data acquisition, which was included in the header.
- `x`: An array of the horizontal values (usually time).
- `y`: An array of vertical values (usually volts).

## SAFT readers

Reads files saved by the SAFT software which was developed at PNNL by the Applied Physics group. Currently is `pandas.Panel` (3-D array types) data type is returned. 

## Ultravision readers

Reads exported ultravision files. Currently supports reading multiple measurements within the same file. 

If the read file contains a single measurement, an `xarray` `DataArray` is returned. If multiple measurements are present, a `dict` of `xarray` `DataArrays` is returned.

