from __future__ import annotations
from textwrap import dedent, indent
from collections.abc import Sequence

import numpy as np

from matflow.param_classes.boundary_conditions import BoundaryCondition

_DIR_LOOKUP = {
    "x": "Lx",
    "y": "Ly",
    "z": "Lz",
}


def write_problem_py_script(path, load_case, solver_options):

    TEMPLATE = dedent(
        """\
        import jax
        import jax.numpy as np
        import numpy as onp
        import os
        import time

        from jax_fem.solver import solver
        from jax_fem.generate_mesh import box_mesh, Mesh
        from jax_fem.utils import save_sol


        from model import CrystalPlasticity

        os.environ["CUDA_VISIBLE_DEVICES"] = "2"

        case_name = "{case_name}"

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        vtk_dir = os.path.join(data_dir, f"vtk/{{case_name}}")


        def load_mesh_file():
            mesh_data = onp.load("mesh.npz")
            meshio_obj = box_mesh(*mesh_data["num_cells"], *mesh_data["domain"])
            mesh_obj = Mesh(meshio_obj.points, meshio_obj.cells_dict["hexahedron"], ele_type="HEX8")
            return {{
                "mesh_obj": mesh_obj,
                "cell_grain_indices": mesh_data["cell_grain_indices"],
                "quaternions": mesh_data["quaternions"],
                "grain_orientation_indices": mesh_data["grain_orientation_indices"],
            }}


        def problem():
            print(jax.lib.xla_bridge.get_backend().platform)

            ele_type = "HEX8"

            mesh_data = load_mesh_file()
            mesh = mesh_data["mesh_obj"]
            cell_grain_inds = mesh_data["cell_grain_indices"]
            grain_oris_inds = mesh_data["grain_orientation_indices"]
            cell_ori_inds = grain_oris_inds[cell_grain_inds]
            quat = mesh_data["quaternions"]

            print(f"{{quat=!r}}")
            print("cell_grain_inds", cell_grain_inds)
            print("grain_oris_inds", grain_oris_inds)
            print("cell_ori_inds", cell_ori_inds)
            print("No. of total mesh points:", mesh.points.shape)

            Lx = np.max(mesh.points[:, 0])
            Ly = np.max(mesh.points[:, 1])
            Lz = np.max(mesh.points[:, 2])
            print(f"Domain size: {{Lx}}, {{Ly}}, {{Lz}}")

        {dirichlet_BCs}

            ## Hu: Define CPFEM problem on top of JAX-FEM
            ## Xue, Tianju, et al. Computer Physics Communications 291 (2023): 108802.
            problem = CrystalPlasticity(
                mesh,
                vec=3,
                dim=3,
                ele_type=ele_type,
                dirichlet_bc_info=dirichlet_bc_info,
                additional_info=(quat, cell_ori_inds),
            )

            sol_list = [np.zeros((problem.fes[0].num_total_nodes, problem.fes[0].vec))]
            ## Hu: self.internal_vars = [Fp_inv_gp, slip_resistance_gp, slip_gp, rot_mats_gp]
            params = problem.internal_vars

            results_to_save = []
            stress_plot = np.array([])
            stress_xx_plot = np.array([])
            stress_yy_plot = np.array([])
            stress_zz_plot = np.array([])
            von_mises_stress_plot = np.array([])

            for i in range(len(ts) - 1):
                problem.dt = ts[i + 1] - ts[i]
                print(
                    f"\\nStep {{i + 1}} in {{len(ts) - 1}}, disp = {{displacements[i + 1]}}, dt = {{problem.dt}}"
                )

                ## Hu: Reset Dirichlet boundary conditions.
                ## Hu: Useful when a time-dependent problem is solved, and at each iteration the boundary condition needs to be updated.
                dirichlet_bc_info[-1][{dirichlet_ut_idx}] = constant_value(displacements[i + 1])
                problem.fes[0].update_Dirichlet_boundary_conditions(dirichlet_bc_info)

                ## Hu: Set up internal variables of previous step for inner Newton's method
                ## self.internal_vars = [Fp_inv_gp, slip_resistance_gp, slip_gp, rot_mats_gp]
                problem.set_params(params)

                ## Hu: JAX-FEM's solver for outer Newton's method
                ## solver(problem, solver_options={{}})
                ## Examples:
                ## (1) solver_options = {{'jax_solver': {{}}}}
                ## (2) solver_options = {{'umfpack_solver': {{}}}}
                ## (3) solver_options = {{'petsc_solver': {{'ksp_type': 'bcgsl', 'pc_type': 'jacobi'}}, 'initial_guess': some_guess}}
                sol_list = solver(
                    problem, solver_options={{"{solver_name}": {solver_options}, "initial_guess": sol_list}}
                )

                ## Hu: Post-processing for aacroscopic Cauchy stress of each cell
                print(f"Computing stress...")
                sigma_cell_data = problem.compute_avg_stress(sol_list[0], params)[:, :, :]
                sigma_cell_xx = sigma_cell_data[:, 0, 0]
                sigma_cell_yy = sigma_cell_data[:, 1, 1]
                sigma_cell_zz = sigma_cell_data[:, 2, 2]
                sigma_cell_xy = sigma_cell_data[:, 0, 1]
                sigma_cell_xz = sigma_cell_data[:, 0, 2]
                sigma_cell_yz = sigma_cell_data[:, 1, 2]
                sigma_cell_von_mises_stress = (
                    0.5
                    * (
                        (sigma_cell_xx - sigma_cell_yy) ** 2.0
                        + (sigma_cell_yy - sigma_cell_zz) ** 2.0
                        + (sigma_cell_zz - sigma_cell_xx) ** 2.0
                    )
                    + +3.0 * (sigma_cell_xy**2.0 + sigma_cell_yz**2.0 + sigma_cell_xz**2.0)
                ) ** 0.5

                stress_xx_plot = np.append(stress_xx_plot, np.mean(sigma_cell_xx))
                stress_yy_plot = np.append(stress_yy_plot, np.mean(sigma_cell_yy))
                stress_zz_plot = np.append(stress_zz_plot, np.mean(sigma_cell_zz))
                von_mises_stress_plot = np.append(
                    von_mises_stress_plot, np.mean(sigma_cell_von_mises_stress)
                )
                print(
                    f"Average Cauchy stress: stress_xx = {{stress_xx_plot[-1]}}, stress_yy = {{stress_yy_plot[-1]}}, stress_zz = {{stress_zz_plot[-1]}}, \\
                vM_stress = {{von_mises_stress_plot[-1]}}, max stress = {{np.max(sigma_cell_data)}}"
                )

                ## Hu: Update internal variables
                ## self.internal_vars = [Fp_inv_gp, slip_resistance_gp, slip_gp, rot_mats_gp]
                print(f"Updating int vars...")
                params = problem.update_int_vars_gp(sol_list[0], params)
                F_p_zz, slip_resistance_0, slip_0 = problem.inspect_interval_vars(params)

                ## Hu: Post-processing for visualization
                vtk_path = os.path.join(vtk_dir, f"u_{{i:03d}}.vtu")
                save_sol(
                    problem.fes[0],
                    sol_list[0],
                    vtk_path,
                    cell_infos=[
                        ("cell_ori_inds", cell_ori_inds),
                        ("sigma_xx", sigma_cell_xx),
                        ("sigma_yy", sigma_cell_yy),
                        ("sigma_zz", sigma_cell_zz),
                        ("von_Mises_stress", sigma_cell_von_mises_stress),
                    ],
                )

            print("*************")
            print("grain_oris_inds:\\n", grain_oris_inds)
            print("stress_xx:\\n", onp.array(stress_xx_plot, order="F", dtype=onp.float64))
            print("stress_yy:\\n", onp.array(stress_yy_plot, order="F", dtype=onp.float64))
            print("stress_zz:\\n", onp.array(stress_zz_plot, order="F", dtype=onp.float64))
            print(
                "von_mises_stress:\\n",
                onp.array(von_mises_stress_plot, order="F", dtype=onp.float64),
            )
            print("*************")


        if __name__ == "__main__":
            start_time = time.time()
            problem()
            end_time = time.time()
            run_time = end_time - start_time
            print("Simulation time:", run_time)
        """
    )

    dirichlet_BCs, dirichlet_ut_idx = create_JAX_CPFEM_boundary_conditions_code(
        load_case=load_case, domain_size=["Lx", "Ly", "Lz"]
    )

    INDENT = "    "
    solver_name = solver_options.pop("name")
    with path.open("wt") as fh:
        fh.write(
            TEMPLATE.format(
                case_name="polycrystal",
                dirichlet_BCs=indent(dirichlet_BCs, INDENT),
                dirichlet_ut_idx=dirichlet_ut_idx,
                solver_name=solver_name,
                solver_options=solver_options,
            )
        )


def __apply_for_values(
    dir_BC, func_name, loc_funcs, vec_comps, value_funcs
) -> tuple[str, int | None]:
    out = ""
    dirichlet_update_idx = None
    for field_dir, value in dir_BC.value.items():
        loc_funcs.append(func_name)
        vec_comps.append(BoundaryCondition._DIRS.index(field_dir))
        if value == 0:
            # a function that takes a point and returns zero:
            value_str = "zero_value"
            if value_str not in value_funcs:
                out += dedent(
                    """\
                def zero_value(point):
                    return 0

                """
                )
        elif value.lower() == "u(t)":
            # a function that takes a point and returns the required
            # displacement at time t:
            dirichlet_update_idx = len(value_funcs)
            value_str = "constant_value(displacements[0])"
            if value_str not in value_funcs:
                out += dedent(
                    """\
                def constant_value(value):
                    def val_fn(point):
                        return value
                    return val_fn

                """
                )

        value_funcs.append(value_str)
    return out, dirichlet_update_idx


def create_JAX_CPFEM_boundary_conditions_code(
    load_case, domain_size: Sequence[float | str]
) -> tuple[str, int]:
    """
    Create a string containing Python code that can be used to define this
    load case (represented with Dirichlet boundary conditions) when using JAX-CPFEM.
    """

    dir_BCs = load_case.to_dirichlet_BCs()
    step = load_case.steps[0]

    domain_size_arr = np.asarray(domain_size)
    func_lst = set()
    out = ""
    dirichlet_update_idx = None
    loc_funcs = []
    vec_comps = []
    value_funcs = []
    for dir_BC in dir_BCs:
        corners = dir_BC.corners
        faces = dir_BC.faces
        num_regions = len(corners) if corners else len(faces)
        for corner in corners or ():
            func_name = BoundaryCondition._JAX_CPFEM_BC_FUNC_CORNER_MAP[tuple(corner)]
            if func_name not in func_lst:
                func_lst.update(func_name)
                # apply domain size:
                corner_arr = np.asarray(corner)
                is_max = corner_arr == 1
                corner_arr[is_max] = domain_size_arr[is_max]
                out += BoundaryCondition.get_corner_location_func_str(corner_arr)
            out_i, update_idx = __apply_for_values(
                dir_BC, func_name, loc_funcs, vec_comps, value_funcs
            )
            out += out_i

            if update_idx is not None:
                dirichlet_update_idx = update_idx

        for face in faces or ():
            func_name = BoundaryCondition._JAX_CPFEM_BC_FUNC_FACE_MAP[face]
            if func_name not in func_lst:
                func_lst.update(func_name)
                out += BoundaryCondition.get_face_location_func_str(face, domain_size)
            out_i, update_idx = __apply_for_values(
                dir_BC, func_name, loc_funcs, vec_comps, value_funcs
            )
            out += out_i
            if update_idx is not None:
                dirichlet_update_idx = update_idx

    out += dedent(
        """\
        displacements = np.linspace(0, {strain}*{domain_i}, {num_increments} + 1)
        ts = np.linspace(0, {total_time}, {num_increments} + 1)

        dirichlet_bc_info = [
            {location_functions_str},
            {vector_components_str},
            {value_functions_str},
        ]
    """
    ).format(
        strain=step.strain,
        domain_i=_DIR_LOOKUP[step.direction],
        num_increments=step.num_increments,
        total_time=step.total_time,
        location_functions_str="[" + ", ".join(loc_funcs) + "]",
        vector_components_str="[" + ", ".join(str(i) for i in vec_comps) + "]",
        value_functions_str="[" + ", ".join(value_funcs) + "]",
    )

    return out, dirichlet_update_idx
