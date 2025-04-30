import os, sys
import numpy as np
from pathlib import Path


def full_strain_tensor_loading(
        exadis_path: str,
        Lbox: float,
        nodes,
        segs,
        strain_rate: float,
        strain_tensor: list,
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
    from pyexadis_utils import insert_frank_read_src, von_mises


    class SimulationDriver(SimulateNetwork):

        def __init__(self, *args, **kwargs) -> None:
            super(SimulationDriver, self).__init__(*args, **kwargs)

            self.strain_rate_tensor = kwargs.get("strain_rate_tensor")
            state = kwargs.get("state")
            self.MU, self.NU = state["mu"], state["nu"]
            self.LA = 2*self.MU*self.NU/(1-2*self.NU)

        # Override step_update_response() function to apply strain-rate tensor loading
        def step_update_response(self, N: DisNetManager, state: dict):
            """step_update_response: update applied stress and rotation if needed
            """
            if self.loading_mode == 'strain_rate_tensor':

                # get values of plastic strain, plastic spin, and density computed internally in exadis
                dEp, dWp, state["density"] = N.get_disnet(ExaDisNet).net.get_plastic_strain()
                dEp = np.array(dEp).ravel()[[0,4,8,5,2,1]] # xx,yy,zz,yz,xz,xy
                dWp = np.array(dWp).ravel()[[5,2,1]] # yz,xz,xy
                state["dEp"] = dEp
                state["dWp"] = dWp

                # update strain and stress states based on strain rate tensor
                dE = self.strain_rate_tensor * state["dt"]  # modify here to allow full load path control
                dEe = dE - dEp # elastic strain
                dstress = self.LA*np.sum(dEe[0:3])*np.array([1,1,1,0,0,0]) + 2*self.MU*dEe

                # increment stress and strain tensors
                state["applied_stress"] += dstress
                state["Etot"] += dE

                # store strain and stress values used for the output (e.g. von Mises)
                state["strain"] = von_mises(state["Etot"])
                state["stress"] = von_mises(state["applied_stress"])

            else:
                # call base class function
                super().step_update_response(N, state)

            return state


    pyexadis.initialize()

    state = {
        "crystal": 'fcc',
        "burgmag": 2.55e-10,
        "mu": 54.6e9,
        "nu": 0.324,
        "a": 6.0,
        "maxseg": 2000.0,
        "minseg": 300.0,
        "rtol": 10.0,
        "rann": 10.0,
        "nextdt": 1e-10,
        "maxdt": 1e-9,
    }
    print(strain_tensor)

    strain_rate_tensor = strain_rate * np.array(strain_tensor)
    cell = pyexadis.Cell(h=Lbox*np.eye(3), is_periodic=[1, 1, 1])

    G = ExaDisNet(cell, nodes, segs)
    net = DisNetManager(G)

    vis = None

    calforce  = CalForce(force_mode='SUBCYCLING_MODEL', state=state, Ngrid=64, cell=net.cell)
    mobility  = MobilityLaw(mobility_law='FCC_0', state=state, Medge=64103.0, Mscrew=64103.0, vmax=4000.0)
    timeint   = TimeIntegration(integrator='Subcycling', rgroups=[0.0, 100.0, 600.0, 1600.0], state=state, force=calforce, mobility=mobility)
    collision = Collision(collision_mode='Retroactive', state=state)
    topology  = Topology(topology_mode='TopologyParallel', state=state, force=calforce, mobility=mobility)
    remesh    = Remesh(remesh_rule='LengthBased', state=state)

    cross_slip = None
    #cross_slip = CrossSlip(cross_slip_mode='ForceBasedParallel', state=state, force=calforce)

    sim = SimulationDriver(calforce=calforce, mobility=mobility, timeint=timeint, collision=collision,
                           topology=topology, remesh=remesh, cross_slip=cross_slip, vis=vis,
                           loading_mode='strain_rate_tensor', strain_rate_tensor=strain_rate_tensor,
                           max_strain=max_strain, max_step=max_step, burgmag=state["burgmag"], state=state,
                           print_freq=print_freq, write_freq=write_freq, write_dir='./')
    sim.run(net, state)

    pyexadis.finalize()
