import os, sys
import numpy as np


def uniaxial_loading(
        exadis_path: str,
        Lbox: float,
        maxseg: float,
        minseg: float,
        n_sources: int,
        n_nodes_per_source: int,
        strain_rate: float,
        strain_dir: np.array,
        max_strain: float,
        max_step: int,
        print_freq: int,
        write_freq: int,
        seed: int | None,
        ):

    if not exadis_path in sys.path:
        sys.path.append(os.path.abspath(exadis_path))
    np.set_printoptions(threshold=20, edgeitems=5)

    import pyexadis
    from pyexadis_base import ExaDisNet, DisNetManager, SimulateNetwork
    from pyexadis_base import CalForce, MobilityLaw, TimeIntegration, Collision, Remesh, Topology
    from pyexadis_utils import von_mises, insert_frank_read_src


    if seed:
        np.random.default_rng(seed)

    pyexadis.initialize()

    strain_dir = np.array(strain_dir)

    state = {
        "crystal": 'fcc',
        "burgmag": 2.55e-10,
        "mu": 54.6e9,
        "nu": 0.324,
        "a": 6.0,
        "maxseg": maxseg,
        "minseg": minseg,
        "rtol": 10.0,
        "rann": 10.0,
        "nextdt": 1e-10,
        "maxdt": 1e-9,
    }

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
        # np.array([1.0, 0.0, 0.0]),
        # np.array([0.0, 1.0, 0.0]),
        # np.array([0.0, 0.0, 1.0]),

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

    for n in range(n_sources):
        b_idx = np.random.randint(0, len(burgers))
        p_idx = np.random.randint(0, 4)
        b = burgers[b_idx]
        p = planes[int(habit_plane_idx[b_idx, p_idx])]
        length = (np.random.rand(1) + 0.5) / 1.5 * Lbox / 2.0
        center = np.random.rand(3)*Lbox
        nodes, segs = insert_frank_read_src(cell, nodes, segs, b, p, length, center, numnodes=n_nodes_per_source)

    G = ExaDisNet(cell, nodes, segs)
    net = DisNetManager(G)

    calforce  = CalForce(force_mode='SUBCYCLING_MODEL', state=state, Ngrid=64, cell=net.cell)
    mobility  = MobilityLaw(mobility_law='FCC_0', state=state, Medge=64103.0, Mscrew=64103.0, vmax=4000.0)
    timeint   = TimeIntegration(integrator='Subcycling', rgroups=[0.0, 100.0, 600.0, 1600.0], state=state, force=calforce, mobility=mobility)
    collision = Collision(collision_mode='Retroactive', state=state)
    topology  = Topology(topology_mode='TopologyParallel', state=state, force=calforce, mobility=mobility)
    remesh    = Remesh(remesh_rule='LengthBased', state=state)

    cross_slip = None
    #cross_slip = CrossSlip(cross_slip_mode='ForceBasedParallel', state=state, force=calforce)

    sim = SimulateNetwork(calforce=calforce, mobility=mobility, timeint=timeint, collision=collision,
                              topology=topology, remesh=remesh, cross_slip=cross_slip, vis=None,
                              loading_mode='strain_rate', erate=strain_rate, edir=strain_dir,
                              max_strain=max_strain, max_step=max_step, burgmag=state["burgmag"], state=state,
                              print_freq=print_freq, plot_pause_seconds=0.0001,
                              write_freq=write_freq, write_dir='./')
    sim.run(net, state)

    pyexadis.finalize()
