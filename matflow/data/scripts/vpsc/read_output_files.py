from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def read_output_files(path):
    volume_response = {}

    # Read average stress/strain output file
    strstr_data = {}
    strstr_incs = {}

    inc = 0
    with path.open(mode='r') as f:
        for line in f:
            line = line.split()
            if str(line[0]).lower() == 'evm':
                # Header row
                headers = [str(header) for header in line]
                for header in headers:
                    if header not in strstr_data:
                        strstr_data[header] = []
                        strstr_incs[header] = []
                first_data_line = True
            else:
                # Data row
                if not first_data_line or inc == 0:
                    for header, val in zip(headers, line):
                        strstr_data[header].append(float(val))
                        strstr_incs[header].append(inc)
                    inc += 1
                first_data_line = False

    header_conv = {
        'Evm': ('avg_equivalent_strain', 'von Mises true strain'),
        'Svm': ('avg_equivalent_stress', 'von Mises Cauchy stress'),
        'E': ('avg_strain', 'True strain'),
        'SCAU': ('avg_stress', 'Cauchy stress'),
        'SDEV': ('avg_deviatoric_stress', 'Deviatoric Cauchy stress'),
        'TEMP': ('avg_temperature', 'Temperature'),
    }

    tensors_done = []
    for header in strstr_data.keys():
        try:
            int(header[-1])
            # tensor output
            header = header[:-2]
            if header in tensors_done:
                continue
            tensors_done.append(header)

            data = np.vstack([strstr_data[header + v]
                              for v in ('11', '22', '33', '23', '13', '12')])
            data = vec6_to_tensor33sym(data.T)
            incs = strstr_incs[header + '11']

        except ValueError:
            # scalar output
            data = np.array(strstr_data[header])
            incs = strstr_incs[header]

        volume_response.update({
            header_conv[header][0]: {
                'data': data,
                'meta': {
                    'increments': incs,
                    'notes': header_conv[header][1]
                }
            }
        })

    strain_vm = volume_response['avg_equivalent_strain']['data']

    # Read orientations output file
    # num_phases = 1
    # for phase in range(num_phases):
    phase = 0
    path_tex = path.parent / f'TEX_PH{phase+1}.OUT'

    incs = []
    num_oris = None
    all_oris = []
    with path_tex.open(mode='r') as f:
        try:
            while True:
                strain = float(next(f).split()[-1])
                # Find what inc this is by matching VM strain
                # Cast to python int to stop weird behaviour saving to hdf
                inc = int(np.argmin(np.abs(strain_vm - strain)))
                # Skip last inc if it is repeated
                if num_oris is not None and inc == incs[-1]:
                    break
                incs.append(inc)

                next(f)
                next(f)
                # elps_axes = [float(x) for x in next(f).split()[:3]]
                # elps_ori = [float(x) for x in next(f).split()[:3]]
                conv, num_oris_in = next(f).split()
                num_oris_in = int(num_oris_in)

                assert conv == 'B'
                if num_oris is None:
                    num_oris = num_oris_in
                else:
                    assert num_oris_in == num_oris

                oris = np.loadtxt(f, max_rows=num_oris, usecols=[0, 1, 2])

                all_oris.append(oris)
        except StopIteration:
            pass

    all_oris = np.array(all_oris)

    volume_response.update({
        'O': {
            'data': {
                'type': 'euler',
                'euler_angles': all_oris,
                'unit_cell_alignment': {'x': 'a'},
                'euler_degrees': True,
            },
            'meta': {
                'increments': incs,
            }
        }
    })

    orientations_response = {
        'volume_data': volume_response,
    }
    return orientations_response
