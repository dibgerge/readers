from struct import unpack
import numpy as np
from datetime import datetime


def read_lecroy(filename):
    """
    Reads binary waveform file (.trc) saved from LeCroy Waverunner Oscilloscope.

    Parameters
    ----------
    filename : string
        The LeCroy binary file to be loaded. The full path or absolute path must be given.

    Returns
    -------
    wave : Dict
        A dictionary `wave` with three keys is returned:
        wave['x'] is the horizontal axis of the data acquistion
        wave['y'] is the vertical axis of the data aquisition
        wave['info'] is itself a dictionary containing information
        about the data acquisiton. The keys for wave info are:

        ===============   =============================================================
        Key               Description
        ===============   =============================================================
        instrument_name   Name of the oscilloscope
        instrument_name   Unique serial number of oscilloscope
        filename          The loaded file name
        trigger_time      A datetime object for trigger time with microsecond accuracy
        channel           Channel number
        coupling          Channel coupling possible values are: DC_50ohms,
                          Ground, DC_10Mohm, AC_1Mohm
        bandwidth_limit   Boolean indicating if bandwidth limit was used on the channel
        record type       Possible values: single_sweep, interleaved, histogram, graph
                          filter_coefficient, complex, extrema,
                          sequence_obsolete, contered_RIS, peak_detect
        processing        Type of processing done on the waveform:
                          no_processing, fir_filter, interpolated,
                          sparsed, autoscaled, no_result, rolling, cumulative
        nominal_bits      Number of bits for oscilloscope
        gain_with_probe   Gain in volts/div
        timebase          seconds/div
        Fs                Sampling frequency (samples/second)
        Ts                Sampling time (seconds/sample)
        ===============   =============================================================

    References
    ----------
    This function is based on the Matlab file ReadLeCroyBinaryWaveform.m
    by Jean-Daniel Deschenes,and also it is an adaptation (fixing multiple
    bugs), from the file website
    http://qtwork.tudelft.nl/gitdata/users/guen/qtlabanalysis/analysis_modules/general/lecroy.py
    """

    # Define an empty dictionary that will be used to store wave info
    info = {}

    # Seek offset in the header block
    fid = open(filename, "rb")
    data = fid.read(50)
    WAVEDESC = str.find(data.decode('UTF-8'), 'WAVEDESC')

    # ------------------------------------------------------------------------
    # Define the addresses of the various informations in the file
    # These addresses are valid for the template LECROY_2_2 and are subject
    # to change in future revisions of the LeCroy firmware
    # ------------------------------------------------------------------------
    TESTED_TEMPLATE = 'LECROY_2_3'

    # Addresses (WAVEDESC + address as stated in the LECROY template)
    aTEMPLATE_NAME = WAVEDESC + 16
    aCOMM_TYPE = WAVEDESC + 32
    aCOMM_ORDER = WAVEDESC + 34
    aWAVE_DESCRIPTOR = WAVEDESC + 36  # length of the descriptor block
    aUSER_TEXT = WAVEDESC + 40        # length of the usertext block
    aTRIGTIME_ARRAY = WAVEDESC + 48   # length of the TRIGTIME array
    aWAVE_ARRAY_1 = WAVEDESC + 60     # length (in Byte) of the sample array
    aINSTRUMENT_NAME = WAVEDESC + 76
    aINSTRUMENT_NUMBER = WAVEDESC + 92
    # aTRACE_LABEL = WAVEDESC + 96
    # aWAVE_ARRAY_COUNT = WAVEDESC + 116
    aSUBARRAY_COUNT = WAVEDESC + 144
    aVERTICAL_GAIN = WAVEDESC + 156
    aVERTICAL_OFFSET = WAVEDESC + 160
    aNOMINAL_BITS = WAVEDESC + 172
    aHORIZ_INTERVAL = WAVEDESC + 176
    aHORIZ_OFFSET = WAVEDESC + 180
    # aVERTUNIT = WAVEDESC + 196
    # aHORUNIT = WAVEDESC + 244
    aTRIGGER_TIME = WAVEDESC + 296
    aRECORD_TYPE = WAVEDESC + 316
    aPROCESSING_DONE = WAVEDESC + 318
    aTIMEBASE = WAVEDESC + 324
    aVERT_COUPLING = WAVEDESC + 326
    aPROBE_ATT = WAVEDESC + 328
    aFIXED_VERT_GAIN = WAVEDESC + 332
    aBANDWIDTH_LIMIT = WAVEDESC + 334
    # aVERTICAL_VERNIER = WAVEDESC + 336
    # aACQ_VERT_OFFSET = WAVEDESC + 340
    aWAVE_SOURCE = WAVEDESC + 344

    # -------------------------------------------------------------------------
    # determine the number storage format HIFIRST / LOFIRST
    # (big endian / little endian)
    # -------------------------------------------------------------------------
    fid.seek(aCOMM_ORDER)
    COMM_ORDER = ord(fid.read(1))

    if COMM_ORDER == 0:
        # big-endian
        fmt = '>'
    else:
        # little-endian
        fmt = '<'

    # -------------------------------------------------------------------------
    # Get the waveform information
    # -------------------------------------------------------------------------
    TEMPLATE_NAME = _readString(fid, fmt, aTEMPLATE_NAME).rstrip('\n\t\r\0')
    if TEMPLATE_NAME != TESTED_TEMPLATE:
        print("WARNING!")
        print("This function has been written for the LeCroy Template %s.\n"
              "The current file contains information created with the "
              "template %s." % (TESTED_TEMPLATE, TEMPLATE_NAME))

    # Instrument information
    info['instrument_name'] = _readString(fid, fmt,
                                          aINSTRUMENT_NAME).rstrip('\0')
    info['instrument_number'] = _readLong(fid, fmt, aINSTRUMENT_NUMBER)
    info['filename'] = filename

    # Channel information
    info['trigger_time'] = _readTimeStamp(fid, fmt, aTRIGGER_TIME)
    info['channel'] = _readWord(fid, fmt, aWAVE_SOURCE)+1
    info['coupling'] = ['DC_50ohms',
                        'Ground',
                        'DC_10Mohm',
                        'Ground',
                        'AC_1Mohm'][_readWord(fid, fmt, aVERT_COUPLING)]
    info['bandwidth_limit'] = bool(_readWord(fid, fmt, aBANDWIDTH_LIMIT))
    info['record_type'] = ['single_sweep',
                           'interleaved',
                           'histogram',
                           'graph',
                           'filter_coefficient',
                           'complex',
                           'extrema',
                           'sequence_obsolete',
                           'contered_RIS',
                           'peak_detect'][_readWord(fid, fmt, aRECORD_TYPE)]
    info['processing'] = ['no_processing',
                          'fir_filter',
                          'interpolated',
                          'sparsed',
                          'autoscaled',
                          'no_result',
                          'rolling',
                          'cumulative'][_readWord(fid, fmt,
                                                  aPROCESSING_DONE)]

    # Vertical axis settings
    e = _readWord(fid, fmt, aFIXED_VERT_GAIN)
    FIXED_VERT_GAIN = [1, 2, 5][e % 3]*(10**(np.floor(e/3)-6))
    PROBE_ATT = _readFloat(fid, fmt, aPROBE_ATT)
    VERTICAL_GAIN = _readFloat(fid, fmt, aVERTICAL_GAIN)
    VERTICAL_OFFSET = _readFloat(fid, fmt, aVERTICAL_OFFSET)

    info['nominal_bits'] = _readWord(fid, fmt, aNOMINAL_BITS)
    info['gain_with_probe'] = FIXED_VERT_GAIN*PROBE_ATT

    # Horizontal settings
    HORIZ_INTERVAL = _readFloat(fid, fmt, aHORIZ_INTERVAL)
    HORIZ_OFFSET = _readDouble(fid, fmt, aHORIZ_OFFSET)

    e = _readWord(fid, fmt, aTIMEBASE)
    info['timebase'] = [1, 2, 5][e % 3]*(10**(np.floor(e/3)-12))
    info['Fs'] = 1/HORIZ_INTERVAL
    info['Ts'] = HORIZ_INTERVAL

    # Read samples array (Plain binary ADC values)
    COMM_TYPE = _readWord(fid, fmt, aCOMM_TYPE)
    WAVE_DESCRIPTOR = _readLong(fid, fmt, aWAVE_DESCRIPTOR)
    USER_TEXT = _readLong(fid, fmt, aUSER_TEXT)
    TRIGTIME_array = _readLong(fid, fmt, aTRIGTIME_ARRAY)
    WAVE_ARRAY_1 = _readLong(fid, fmt, aWAVE_ARRAY_1)
    info['nb_segments'] = _readLong(fid, fmt, aSUBARRAY_COUNT)

    fid.close()
    fid = open(filename, "rb")

    # Read the actual data
    header_len = WAVEDESC + WAVE_DESCRIPTOR + USER_TEXT + TRIGTIME_array
    y = _readData(fid, fmt, header_len, WAVE_ARRAY_1, commtype=COMM_TYPE)
    y = VERTICAL_GAIN * y - VERTICAL_OFFSET
    x = np.arange(1, len(y)+1)*HORIZ_INTERVAL + HORIZ_OFFSET
    fid.close()
    return {'info': info,
            'x': x,
            'y': y}


def _readString(fid, fmt, Addr):
    """ Read a string up to 16 bytes in length. """
    fid.seek(Addr)
    s = fid.read(16)
    s = unpack(fmt + '16s', s)
    if(type(s) == tuple):
        return s[0].decode('utf-8')
    else:
        return s


def _readByte(fid, fmt, Addr):
    fid.seek(Addr)
    s = fid.read(1)
    s = unpack(fmt + 'b', s)
    if(type(s) == tuple):
        return s[0]
    else:
        return s


def _readWord(fid, fmt, Addr):
    fid.seek(Addr)
    s = fid.read(2)
    s = unpack(fmt + 'h', s)
    if(type(s) == tuple):
        return s[0]
    else:
        return s


def _readLong(fid, fmt, Addr):
    fid.seek(Addr)
    s = fid.read(4)
    s = unpack(fmt + 'l', s)
    if(type(s) == tuple):
        return s[0]
    else:
        return s


def _readFloat(fid, fmt, Addr):
    fid.seek(Addr)
    s = fid.read(4)
    s = unpack(fmt + 'f', s)
    if(type(s) == tuple):
        return s[0]
    else:
        return s


def _readDouble(fid, fmt, Addr):
    fid.seek(Addr)
    s = fid.read(8)
    s = unpack(fmt + 'd', s)
    if(type(s) == tuple):
        return s[0]
    else:
        return s


def _readData(fid, fmt, Addr, datalen, commtype=0):
    fid.seek(Addr)
    data = fid.read()
    result = np.frombuffer(data, dtype=np.int16 if commtype else np.int8)
    return result


def _readTimeStamp(fid, fmt, Addr):
    fid.seek(Addr)
    # s = fid.read(8)
    # print(' '.join(format(ord(x), 'b') for x in s))
    seconds = _readDouble(fid, fmt, Addr)
    minutes = _readByte(fid, fmt, Addr+8)
    hours = _readByte(fid, fmt, Addr+9)
    days = _readByte(fid, fmt, Addr+10)
    months = _readByte(fid, fmt, Addr+11)
    year = _readWord(fid, fmt, Addr+12)
    d = datetime(year=year, month=months, day=days,
                 hour=hours, minute=minutes, second=int(seconds),
                 microsecond=int(np.floor((seconds % 1)*1e6)))
    return d
