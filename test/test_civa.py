import readers
from os.path import join
import unittest
import numpy as np
import pandas.util.testing as pdt
import numpy.testing as npt
import os
import xarray as xr
from matplotlib import pyplot


class TestCIVA(unittest.TestCase):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def test_bscan(self):
        fname = join(self.dir_path, 'data', 'civa_bscan.txt')
        out = readers.read_civa_bscan(fname)
        self.assertIsInstance(out, xr.DataArray)
        self.assertTrue(out.Z.attrs['units'] == 's')
        self.assertTrue(out.X.attrs['units'] == 'mm')
        pyplot.pcolormesh(out.X, out.Z, out)
        pyplot.title('CIVA B-Scan')
        pyplot.show()

    def test_truecscan(self):
        fname = join(self.dir_path, 'data', 'civa_truecscan.grid')
        out = readers.read_civa_tcscan(fname)
        self.assertIsInstance(out, xr.DataArray)
        self.assertTrue(out.X.attrs['units'] == 'mm')
        self.assertTrue(out.Y.attrs['units'] == 'mm')
        pyplot.pcolormesh(out.X, out.Y, out)
        pyplot.title('CIVA True C-SCAN')
        pyplot.show()

    def test_cscan(self):
        fname = join(self.dir_path, 'data', 'civa_cscan.txt')
        out = readers.read_civa_cscan(fname)
        self.assertIsInstance(out, xr.DataArray)
        pyplot.pcolormesh(out.X, out.Y, out)
        pyplot.title('CIVA C-SCAN')
        pyplot.show()


if __name__ == "__main__":
    unittest.main()
