"""
In all of the readers here, we follow the following conventions for naming axes when reading raster
scans or line scans:
- **X**: Name of axis along the Scan direction
- **Y**: Name of axis along the Index direction
- **Z**: Time axis or depth of the specimen

.. currentmodule:: utkit.io

.. autosummary::
    :nosignatures:
    :toctree: generated/

    saft
    lecroy
    ultravision
    civa_bscan
"""
# from __future__ import absolute_import

from .saft import read_saft
from .lecroy import read_lecroy
from .ultravision import read_ultravision
from .civa import *


