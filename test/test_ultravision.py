import readers
from os.path import join
import unittest
import numpy as np
import pandas.util.testing as pdt
import numpy.testing as npt
import os
import xarray as xr


class TestUV(unittest.TestCase):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fname = join(dir_path, 'data', 'ultravision_example_pa.txt')

    # file has 12 angles
    ntheta = 12

    def test_no_parameters(self):
        out = readers.ultravision(self.fname)
        self.assertIsInstance(out, dict)

    def test_with_parameters(self):
        out = readers.ultravision(self.fname, [45] * self.ntheta, 100e6, 3260)
        self.assertIsInstance(out, xr.DataArray)
        self.assertTrue(out.coords['X'].attrs['units'] == 'mm')
        self.assertTrue(out.coords['Y'].attrs['units'] == 'mm')
        self.assertTrue(out.coords['Z'].attrs['units'] == 's')

    def test_wrong_parameters(self):
        """ Did not supply the correct number of angles to the file."""
        self.assertRaises(ValueError, lambda: readers.ultravision(self.fname,
                                                                  [45] * (self.ntheta - 2),
                                                                  100e6, 3260))


if __name__ == "__main__":
    unittest.main()