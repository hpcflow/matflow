import numpy as np
import pyvista as pv
from pyvista.core.utilities import VtkErrorCatcher


SHAPES = {
    "stress_x": (3,),
    "stress_y": (3,),
    "stress_z": (3,),
    "disp_": (3,),
}


def parse_exodus(moose_exodus_file, FE_response_data):

    with VtkErrorCatcher(send_to_logging=False):
        # note: this context manager reduces the output to stderr from VTK, but we still
        # currently get some output, and I can't find a way to silence it.

        path = moose_exodus_file[0]  # list because the file is defined as a regex

        reader = pv.ExodusIIReader(path)
        times = reader.time_values

        reader.set_active_time_point(0)
        mesh = reader.read()
        dataset = mesh.combine()
        num_nodes = dataset.points.shape[0]
        num_incs = len(times)

        FE_response = {
            "times": times,
            "node_coordinates": np.empty((len(times), num_nodes, 3)),
        }
        for key in FE_response_data:
            new_shape = (len(times), num_nodes, *SHAPES.get(key, tuple()))
            FE_response[key] = np.empty(new_shape)

        for time_idx in range(num_incs):
            if time_idx > 0:
                reader.set_active_time_point(time_idx)
                mesh = reader.read()
                dataset = mesh.combine()
            FE_response["node_coordinates"][time_idx] = dataset.points
            for key in FE_response_data:
                FE_response[key][time_idx] = dataset.point_data[key]

    return FE_response
