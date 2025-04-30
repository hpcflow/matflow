import os, sys
import numpy as np
from pathlib import Path


def initial_config_frank_read(
        exadis_path: str,
        Lbox: float,
        n_sources: int,
        seed: int | None,
        ):

    if not exadis_path in sys.path:
        sys.path.append(os.path.abspath(exadis_path))
    np.set_printoptions(threshold=20, edgeitems=5)

    import pyexadis
    from pyexadis_utils import insert_infinite_line

    pyexadis.initialize()

    if seed:
        np.random.default_rng(seed)

    cell = pyexadis.Cell(h=Lbox*np.eye(3), is_periodic=[1, 1, 1])
    nodes, segs = [], []
    burgers = [
        np.sqrt(2.0)/2.0*np.array([1.0, 1.0, 0.0]),
        np.sqrt(2.0)/2.0*np.array([-1.0, 1.0, 0.0]),
        np.sqrt(2.0)/2.0*np.array([1.0, -1.0, 0.0]),
        np.sqrt(2.0)/2.0*np.array([-1.0, -1.0, 0.0]),
        np.sqrt(2.0)/2.0*np.array([1.0, 0.0, 1.0]),
        np.sqrt(2.0)/2.0*np.array([-1.0, 0.0, 1.0]),
        np.sqrt(2.0)/2.0*np.array([1.0, 0.0, -1.0]),
        np.sqrt(2.0)/2.0*np.array([-1.0, 0.0, -1.0]),
        np.sqrt(2.0)/2.0*np.array([0.0, 1.0, 1.0]),
        np.sqrt(2.0)/2.0*np.array([0.0, -1.0, 1.0]),
        np.sqrt(2.0)/2.0*np.array([0.0, 1.0, -1.0]),
        np.sqrt(2.0)/2.0*np.array([0.0, -1.0, -1.0]),
        ]
    planes = [
        np.array([1.0, 1.0, 1.0]),
        np.array([-1.0, 1.0, 1.0]),
        np.array([1.0, -1.0, 1.0]),
        np.array([1.0, 1.0, -1.0]),
        np.array([-1.0, -1.0, 1.0]),
        np.array([1.0, -1.0, -1.0]),
        np.array([-1.0, 1.0, -1.0]),
        np.array([-1.0, -1.0, -1.0])
    ]

    # Get orthogonality matrix to compare Burger's vectors with habit planes
    habit_plane_idx = np.zeros((12, 4))
    for i, b in enumerate(burgers):
        counter = 0
        for j, p in enumerate(planes):
            check = np.dot(b, p)
            if check == 0.0:
                habit_plane_idx[i, counter] = j
                counter += 1

    # Insert sources
    for _ in range(n_sources):
        b_idx = np.random.randint(0, len(burgers))
        p_idx = np.random.randint(0, 4)
        b = burgers[b_idx]
        p = planes[int(habit_plane_idx[b_idx, p_idx])]
        origin = np.random.rand(3)*Lbox
        nodes, segs = insert_infinite_line(cell, nodes, segs, b, p, origin, theta=0.0)

    return {'Lbox': Lbox, 'nodes': nodes, 'segs': segs}
