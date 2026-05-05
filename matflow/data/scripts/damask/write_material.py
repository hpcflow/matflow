from __future__ import annotations
import copy
from pathlib import Path
from damask_parse.writers import write_material as write_material_


def write_material(
    path: Path | str,
    volume_element: dict,
    homogenization: dict,
    damask_phases: dict,
    single_crystal_parameters: dict,
):
    """Write the material.yaml file for a DAMASK simulation.

    Parameters
    ----------
    path
        Full path to the material file to write.
    volume_element
        Volume element data to include in the material file. Allowed keys are:
            orientations : dict
                Dict containing the following keys:
                    type : str
                        One of "euler", "quat".
                    quaternions : ndarray of shape (R, 4) of float, optional
                        Array of R row four-vectors of unit quaternions. Specify either
                        `quaternions` or `euler_angles`.
                    euler_angles : ndarray of shape (R, 3) of float, optional
                        Array of R row three-vectors of Euler angles in degrees or
                        radians, as determined by `euler_degrees`. Specify either
                        `quaternions` or `euler_angles`. Specified as proper Euler
                        angles in the Bunge convention.
                        (Rotations are about Z, new X, new new Z.)
                    euler_degrees : bool, optional
                        If True, `euler_angles` are expected in degrees, rather than
                        radians.
                    unit_cell_alignment : dict
                        Alignment of the unit cell.
            constituent_material_idx : list or ndarray of shape (N,) of int, optional
                Determines the material to which each constituent belongs, where N is the
                number of constituents. If `constituent_*` keys are not specified, then
                `element_material_idx` and `grid_size` must be specified. See Notes.
            constituent_material_fraction: list or ndarray of shape (N,) of float, optional
                The fraction that each constituent occupies within its respective
                material, where N is the number of constituents. If `constituent_*` keys
                are not specified, then `element_material_idx` and `grid_size` must be
                specified. See Notes.
            constituent_phase_label : list or ndarray of shape (N,) of str, optional
                Determines the phase label of each constituent, where N is the number of
                constituents.  If `constituent_*` keys are not specified, then
                `element_material_idx` and `grid_size` must be specified. See Notes.
            constituent_orientation_idx : list or ndarray of shape (N,) of int, optional
                Determines the orientation (as an index into `orientations`) associated
                with each constituent, where N is the number of constituents. If
                `constituent_*` keys are not specified, then `element_material_idx` and
                `grid_size` must be specified. See Notes.
            material_homog : list or ndarray of shape (M,) of str, optional
                Determines the homogenization scheme (from a list of available
                homogenization schemes defined elsewhere) to which each material belongs,
                where M is the number of materials. If `constituent_*` keys are not
                specified, then `element_material_idx` and `grid_size` must be specified.
                See Notes.
            element_material_idx : list or ndarray of shape (P,) of int, optional
                Determines the material to which each geometric model element belongs,
                where P is the number of elements. If `constituent_*` keys are not
                specified, then `element_material_idx` and `grid_size` must be specified.
                See Notes.
            grid_size : list or ndarray of shape (3,) of int, optional
                Geometric model grid dimensions. If `constituent_*` keys are not
                specified, then `element_material_idx` and `grid_size` must be specified.
                See Notes.
            phase_labels : list or ndarray of str, optional
                List of phase labels to associate with the constituents. Only applicable
                if `constituent_*` keys are not specified. The first list element is the
                phase label that will be associated with all of the geometrical elements
                for which an orientation is also specified. Additional list elements are
                phase labels for geometrical elements for which no orientations are
                specified.
            homog_label : str, optional
                The homogenization scheme label to use for all materials in the volume
                element. Only applicable if `constituent_*` keys are not specified.
    homogenization
        Dict whose keys are homogenization scheme labels and whose values are dicts that
        specify the homogenization parameters for that scheme. This will be passed into
        the "homogenization" dict in the material file.
    damask_phases
        Dict whose keys are phase labels and whose values are the dicts that specify the
        phase parameters for that phase label. This will be passed into the "phase" dict
        in the material file.
    single_crystal_parameters
        Properties of the individual crystals.

    Notes
    -----
    - A "material" is currently known as a "microstructure" in the DAMASK material.yml
      file. A "material" may have multiple constituents (e.g. grains), modelled together
      under some homogenization scheme. For a full-field simulation, there will be only
      one constituent per "material" (and no associated homogenization).

    - The input `volume_element` can be either fully specified with respect to the
      `constituent_*` keys or, if no `constituent_*` keys are specified, but the
      `element_material_idx` and `grid_size` keys are specified, we assume the model to be
      a full-field model for which each material contains precisely one constituent. In
      this case the additional keys `phase_labels` and `homog_labels` must be specified.
      The number of phase labels specified should be equal to the number or orientations
      specified plus the total number of any additional material indices in
      "element_material_idx" for which there are no orientations.

    """
    if single_crystal_parameters is not None:
        # merge single-crystal properties into phases:
        damask_phases = copy.deepcopy(damask_phases)
        for phase_label in damask_phases.keys():
            SC_params_name = damask_phases[phase_label]["mechanical"]["plastic"].pop(
                "single_crystal_parameters", None
            )
            if SC_params_name:
                SC_params = single_crystal_parameters[SC_params_name]
                damask_phases[phase_label]["mechanical"]["plastic"].update(**SC_params)

    path_ = Path(path)
    write_material_(
        dir_path=path_.parent,
        homog_schemes=homogenization,
        phases=damask_phases,
        volume_element=volume_element,
        name=path_.name,
    )
