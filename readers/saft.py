import numpy as np
import pandas as pd


def saft(fname):
    """
    Reads a binary file stored in SAFT format. SAFT is a custom scanner at PNNL.

    Parameters
    ----------
    fname : string
        Name of the file to open (with absolute or relative path).

    Returns
    -------
    : utkit.Signal3D, header
        A 2-element tuple where the first element is the Signal3D stored in the SAFT file,
        returned as a :class:`utkit.Signal3D` object. The second element is a dictionary
        representing the SAFT file header fields.
    """
    # Number of bytes in the file header
    NHEADER = 2**11
    fid = open(fname, 'rb')
    htext = fid.read(NHEADER)
    header = _read_header(htext)
    data_type = 'uint16' if header['data_16bit'] else 'uint8'
    nbits = 8 + 8*header['data_16bit']
    data = np.frombuffer(fid.read(), dtype=data_type)
    fid.close()

    Nx = header['scan_xpoints']
    Ny = header['scan_ypoints']
    Ns = header['samp_ascan_length']
    len_data_header = 2**5/(nbits/8)

    # verify that the file is intact, and reading is correct
    computed_nascans = len(data)/(Ns+len_data_header)
    if computed_nascans != Nx*Ny:
        raise IOError("The number of A-scans is incorrect. Possibly corrupt reading.")
    # remove the data header before each A-scan
    data = data.reshape(Ny, Nx, Ns+len_data_header)[:, :, len_data_header:]
    data = np.transpose(data.astype('float') - 2**(nbits-1), (0, 2, 1))
    header['sampling_rate'] = Ns*1e9/(header['samp_windowstop_ns'] - header['samp_windowstart_ns'])
    # the constant 1e-9 is to convert from nanosecond to second
    t = header['samp_windowstart_ns']*1e-9 + np.arange(Ns)/header['sampling_rate']

    # the hardcoded constant 25.4e-3 is to convert from inches to meters
    X = np.arange(header['scan_xpoints'])*header['scan_xstep_in']*25.4e-3
    Y = np.arange(header['scan_ypoints'])*header['scan_ystep_in']*25.4e-3
    return pd.Panel(data, items=Y, major_axis=t, minor_axis=X), header


def _header_field(htext, start_ind, field_len, dtype=None):
    """ Reads a specified field in the SAFT header."""
    special_chars = '\xcd\x00\x20'
    field = htext[start_ind:start_ind+field_len].decode(errors='ignore').strip(special_chars)

    if dtype is None:
        # if no data type is given, try to convert to float,
        # and if a ValueError is caught, output string type
        try:
            out = float(field)
        except ValueError:
            out = field
    else:
        try:
            out = dtype(field)
        except:
            raise ValueError("Cannot convert header field to given data type.")

    return start_ind + field_len, out


def _read_header(htext):
    """
    Reads a SAFT header into corresponding fields
    """
    header = {}
    n = 0
    # ----------------------- General Fields ------------------------------#
    n, header['ascii'] = _header_field(htext, n, 10, dtype=str)
    n, header['title'] = _header_field(htext, n, 81)
    n, header['date'] = _header_field(htext, n, 9)
    n, header['time'] = _header_field(htext, n, 9)

    # ----------------------- Data Fields ------------------------------#
    # 0 = time, 1 = frequency
    n, header['data_domain'] = _header_field(htext, n, 2, dtype=int)
    n, header['data_nsets'] = _header_field(htext, n, 12, dtype=int)
    n, header['data_min'] = _header_field(htext, n, 7)
    n, header['data_max'] = _header_field(htext, n, 7)
    n, header['data_avg'] = _header_field(htext, n, 17)
    # 0 = No, 1 = Yes
    n, header['data_projection'] = _header_field(htext, n, 4, dtype=int)
    # 0 = inches
    n, header['data_units'] = _header_field(htext, n, 2, dtype=int)
    # 16-bit data if True. 8-bit if False
    n, header['data_16bit'] = _header_field(htext, n, 7, dtype=int)
    header['data_16bit'] = bool(header['data_16bit'])
    n, header['data_scal_filename'] = _header_field(htext, n, 51)

    # ----------------------- Probe Fields ------------------------------#
    n, header['probe_comment'] = _header_field(htext, n, 81)
    n, header['probe_freq_mhz'] = _header_field(htext, n, 17)
    n, header['probe_rxWedgePath_in'] = _header_field(htext, n, 17)
    n, header['probe_txWedgePath_in'] = _header_field(htext, n, 17)
    n, header['probe_rxWedgeVel_in/s'] = _header_field(htext, n, 17)
    n, header['probe_txWedgeVel_in/s'] = _header_field(htext, n, 17)
    n, header['probe_beamDia_in'] = _header_field(htext, n, 17)
    n, header['probe_refracted_deg'] = _header_field(htext, n, 17)
    n, header['probe_incident_deg'] = _header_field(htext, n, 17)
    n, header['probe_skew_deg'] = _header_field(htext, n, 17)
    # 0 = PE, 1 = TSAFT, 2=TSAFT
    n, header['probe_mode'] = _header_field(htext, n, 2, dtype=int)
    n, header['probe_init_xoffset_in'] = _header_field(htext, n, 17)
    n, header['probe_fnumber'] = _header_field(htext, n, 17)
    n, header['probe_xoffset_wedge'] = _header_field(htext, n, 17)
    n, header['probe_yoffset_wedge'] = _header_field(htext, n, 17)
    n, header['probe_reserved'] = _header_field(htext, n, 13)

    # ----------------------- Material Fields ------------------------------#
    n, header['mat_comment'] = _header_field(htext, n, 81)
    n, header['mat_velocity_in/s'] = _header_field(htext, n, 17)
    n, header['mat_refracted_deg'] = _header_field(htext, n, 17)
    n, header['mat_thickness_in'] = _header_field(htext, n, 17)
    n, header['mat_pipeDia_in'] = _header_field(htext, n, 17)
    n, header['mat_trackDia_in'] = _header_field(htext, n, 17)
    # 0 = unknown, 1 = plate, 2 = pipe, 3 = nozzle
    n, header['mat_type'] = _header_field(htext, n, 7, dtype=int)
    n, header['mat_reserved'] = _header_field(htext, n, 23)

    # ----------------------- Sampling Fields ------------------------------#
    n, header['samp_comment'] = _header_field(htext, n, 81)
    n, header['samp_delayinc_ns'] = _header_field(htext, n, 17)
    n, header['samp_initdelay_ns'] = _header_field(htext, n, 17)
    # number of points in an ascan
    n, header['samp_ascan_length'] = _header_field(htext, n, 7, dtype=int)
    # sound path to start of data-window (in)
    n, header['samp_start_in'] = _header_field(htext, n, 17)
    # depth to end of data-window (in)
    n, header['samp_stop_in'] = _header_field(htext, n, 17)
    n, header['samp_averages'] = _header_field(htext, n, 7, dtype=int)
    # minimum time between pulses (s)
    n, header['samp_pulsetime'] = _header_field(htext, n, 17)
    # step along each wave path (in)??
    n, header['samp_step_wavepath_in'] = _header_field(htext, n, 17)
    # start time of sampling in nanoseconds
    n, header['samp_windowstart_ns'] = _header_field(htext, n, 11)
    # Stop time of sampling in nanoseconds
    n, header['samp_windowstop_ns'] = _header_field(htext, n, 11)
    # depth to end of data window??
    n, header['samp_depthend_window'] = _header_field(htext, n, 1)

    # ----------------------- Scan Fields ------------------------------#
    n, header['scan_comment'] = _header_field(htext, n, 81)
    n, header['scan_dir_deg'] = _header_field(htext, n, 17)
    n, header['scan_xstart_in'] = _header_field(htext, n, 17)
    n, header['scan_ystart_in'] = _header_field(htext, n, 17)
    n, header['scan_xstop_in'] = _header_field(htext, n, 17)
    n, header['scan_ystop_in'] = _header_field(htext, n, 17)
    n, header['scan_xstep_in'] = _header_field(htext, n, 17)
    n, header['scan_ystep_in'] = _header_field(htext, n, 17)
    n, header['scan_xpoints'] = _header_field(htext, n, 7, dtype=int)
    n, header['scan_ypoints'] = _header_field(htext, n, 7, dtype=int)
    # 'Y' = scanner points downstream, 'N' = upstream
    n, header['scan_isdownstream'] = _header_field(htext, n, 2, dtype=str)
    n, header['scan_tx_half_vees'] = _header_field(htext, n, 12)
    n, header['scan_rx_half_vees'] = _header_field(htext, n, 12)
    #  number of estimated half V's before signal encounters object plane (arrow)
    n, header['scan_num_halfvees'] = _header_field(htext, n, 17)
    n, header['scan_init_pos'] = _header_field(htext, n, 17)
    n, header['scan_final_pos'] = _header_field(htext, n, 17)
    # 'Y' = collects moving towards, 'N' = away
    n, header['scan_toward_track'] = _header_field(htext, n, 2, dtype=str)
    n, header['scan_scannertype'] = _header_field(htext, n, 4)
    n, header['scan_pattern'] = _header_field(htext, n, 7)
    n, header['scan_zincrement'] = _header_field(htext, n, 17)

    n, header['processing'] = _header_field(htext, n, 308)
    n, header['nozzle'] = _header_field(htext, n, 68)
    n, header['other'] = _header_field(htext, n, 86)
    n, header['TVG'] = _header_field(htext, n, 90)
    # 0=no digitizer, 1=str864, 2=CS12100
    n, header['digi_type'] = _header_field(htext, n, 7, dtype=int)
    # 0 = unknown, 1 = tek bin, 2 = ISA card
    n, header['TVG_type'] = _header_field(htext, n, 7, dtype=int)
    # 0= unknown, 1=pcpr100
    n, header['pulser_type'] = _header_field(htext, n, 7, dtype=int)
    n, header['vpp'] = _header_field(htext, n, 17, dtype=float)
    # 0 = hardware, 1=software, 2=rear mode
    n, header['sync_mode'] = _header_field(htext, n, 7, dtype=int)
    n, header['other2'] = _header_field(htext, n, 179)
    return header
