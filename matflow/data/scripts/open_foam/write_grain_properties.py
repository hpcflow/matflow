from textwrap import dedent
import shutil
from pathlib import Path
import re


def write_grain_properties(path, volume_element, orientations, materials, root_path=None):
    if not materials:
        if root_path is None:
            raise ValueError("root_path is required when materials is not supplied.")
        shutil.copyfile(Path(root_path) / "constant" / "GrainProperties", path)
        return

    import numpy as np

    TEMPLATE = dedent(
        """\
        /*--------------------------------*- C++ -*----------------------------------*\\
        =========                 |
        \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
         \\\\    /   O peration     | Website:  https://openfoam.org
          \\\\  /    A nd           | Version:  10
           \\\\/     M anipulation  |
        \\*---------------------------------------------------------------------------*/
        FoamFile
        {{
            format      ascii;
            class       dictionary;
            location    "constant";
            object      GrainProperties;
        }}
        // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

        interface_width	{interface_width};

        n_constitutive_substeps	{n_constitutive_substeps};

        N_Phases	{num_grains};

        N_Materials	{num_materials};

        Phase2Material ({phase_mat_idx}); // material index for each grain

        phi1 ({phi1});
        phi2 ({phi2});
        phi3 ({phi3});

        // Interface stuff

        Energy
        (
        {interface_energy}
        );

        Mobility
        (
        {interface_mobility}
        );

        {materials}
    """
    )

    MAT_TEMPLATE = dedent(
        R"""
        Material.{mat_idx} // {mat_label}
        {{
        
        {elasticity_tensor}

        N_slips {num_slips};

        {slip_planes}

        {slip_dirs}
        
        {mat_props}

        }}

        // ************************************************************************* //
        """
    )

    grain_phase_labels = volume_element["constituent_phase_label"][:]
    uniq_phase_labs, grain_phase_idx = np.unique(grain_phase_labels, return_inverse=True)
    if len(materials) != len(uniq_phase_labs):
        raise ValueError(
            "The number of supplied materials must equal the number of unique "
            "phase labels in volume_element."
        )

    mat_strs = []
    for mat_idx, mat_i in enumerate(materials):
        slip_sys = mat_i["slip_systems"]

        mat_i_str = MAT_TEMPLATE.format(
            mat_idx=mat_idx,
            mat_label=mat_i["label"],
            elasticity_tensor="\n".join(
                f"{k}    {v:.2E};" for k, v in mat_i["elasticity"].items()
            ),
            num_slips=len(slip_sys),
            slip_planes="\n".join(
                f"m{s_idx:<3}({s_plane[0]:10.3f}{s_plane[1]:10.3f}{s_plane[2]:10.3f});"
                for s_idx, (s_plane, _) in enumerate(slip_sys)
            ),
            slip_dirs="\n".join(
                f"n{s_idx:<3}({s_dir[0]:10.3f}{s_dir[1]:10.3f}{s_dir[2]:10.3f});"
                for s_idx, (_, s_dir) in enumerate(slip_sys)
            ),
            mat_props="\n".join(f"{k:<20} {v};" for k, v in mat_i["properties"].items()),
        )
        mat_strs.append(mat_i_str)

    def tutorial_interface_values(name):
        if root_path is None:
            return {}
        tutorial = (Path(root_path) / "constant" / "GrainProperties").read_text()
        match = re.search(
            rf"\b{name}\b\s*\((.*?)\)\s*;",
            tutorial,
            flags=re.DOTALL,
        )
        if not match:
            return {}
        return {
            (int(i), int(j)): float(value)
            for i, j, value in re.findall(
                r"\(Material\.(\d+) Material\.(\d+)\)\s*([0-9.eE+-]+)",
                match.group(1),
            )
        }

    num_materials = len(uniq_phase_labs)
    tutorial_energy = tutorial_interface_values("Energy")
    tutorial_mobility = tutorial_interface_values("Mobility")
    interface_energy = "\n".join(
        f"(Material.{i} Material.{j}) "
        f"{materials[0].get('interface_energy', tutorial_energy.get((i, j), 0.3 if i != 1 or j != 1 else 0.1))}"
        for i in range(num_materials)
        for j in range(i, num_materials)
    )
    interface_mobility = "\n".join(
        f"(Material.{i} Material.{j}) "
        f"{materials[0].get('interface_mobility', tutorial_mobility.get((i, j), 5.0e-4 if i != j else (5.1e-6 if i == 0 else 5.3e-6)))}"
        for i in range(num_materials)
        for j in range(i, num_materials)
    )

    num_grains = len(np.unique(volume_element["element_material_idx"]))

    assert orientations.representation.type.name == "EULER"
    assert not orientations.representation.euler_is_degrees
    phi1, phi2, phi3 = orientations.data.T

    file_str = TEMPLATE.format(
        interface_width=materials[0].get("interface_width", 4e-6),
        n_constitutive_substeps=materials[0].get("n_constitutive_substeps", 25),
        num_grains=num_grains,
        num_materials=len(uniq_phase_labs),
        phase_mat_idx=" ".join(str(i) for i in grain_phase_idx),
        phi1=" ".join(str(i) for i in phi1),
        phi2=" ".join(str(i) for i in phi2),
        phi3=" ".join(str(i) for i in phi3),
        interface_energy=interface_energy,
        interface_mobility=interface_mobility,
        materials="\n\n".join(mat_strs),
    )
    with path.open("wt") as fp:
        fp.write(file_str)
