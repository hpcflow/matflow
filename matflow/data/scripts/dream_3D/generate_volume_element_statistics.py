from __future__ import annotations
import json
import warnings
import copy
from typing import TYPE_CHECKING
import numpy as np
from numpy.typing import NDArray

from pathlib import Path
from damask_parse.utils import validate_orientations
from damask_parse.quats import axang2quat, multiply_quaternions

if TYPE_CHECKING:
    from matflow.param_classes.orientations import Orientations


REQUIRED_PHASE_BASE_KEYS = {
    "type",
    "name",
    "crystal_structure",
    "volume_fraction",
}
REQUIRED_PHASE_NON_MATRIX_KEYS = REQUIRED_PHASE_BASE_KEYS | {
    "size_distribution",
}
REQUIRED_PHASE_KEYS = {
    "matrix": REQUIRED_PHASE_BASE_KEYS,
    "primary": REQUIRED_PHASE_NON_MATRIX_KEYS,
    "precipitate": REQUIRED_PHASE_NON_MATRIX_KEYS
    | {
        "radial_distribution_function",
        "number_fraction_on_boundary",
    },
}
ALLOWED_PHASE_NON_MATRIX_KEYS = REQUIRED_PHASE_NON_MATRIX_KEYS | {
    "preset_statistics_model",
    "ODF",
    "axis_ODF",
}
ALLOWED_PHASE_KEYS = {
    "matrix": REQUIRED_PHASE_KEYS["matrix"],
    "primary": REQUIRED_PHASE_KEYS["primary"] | ALLOWED_PHASE_NON_MATRIX_KEYS,
    "precipitate": REQUIRED_PHASE_KEYS["precipitate"] | ALLOWED_PHASE_NON_MATRIX_KEYS,
}
ALLOWED_PHASE_TYPES = set(REQUIRED_PHASE_KEYS.keys())
REQUIRED_PHASE_SIZE_DIST_KEYS = {
    "ESD_log_stddev",
}
ALLOWED_PHASE_SIZE_DIST_KEYS = REQUIRED_PHASE_SIZE_DIST_KEYS | {
    "ESD_log_mean",
    "ESD_mean",
    "ESD_log_stddev_min_cut_off",
    "ESD_log_stddev_max_cut_off",
    "bin_step_size",
    "num_bins",
    "omega3",
    "b/a",
    "c/a",
    "neighbours",
}
ALLOWED_PRECIP_RDF_KEYS = {
    "min_distance",
    "max_distance",
    "num_bins",
    "box_size",
}
ALLOWED_CRYSTAL_STRUCTURES = {  # values are crystal symmetry index:
    "hexagonal": 0,
    "cubic": 1,
}
SIGMA_MIN_DEFAULT = 5
SIGMA_MAX_DEFAULT = 5
# Distributions defined for each size distribution bin:
DISTRIBUTIONS_MAP = {
    "omega3": {
        "type": "beta",
        "default_keys": {
            "alpha": 10.0,
            "beta": 1.5,
        },
        "label": "FeatureSize Vs Omega3 Distributions",
    },
    "b/a": {
        "type": "beta",
        "default_keys": {
            "alpha": 10.0,
            "beta": 1.5,
        },
        "label": "FeatureSize Vs B Over A Distributions",
    },
    "c/a": {
        "type": "beta",
        "default_keys": {
            "alpha": 10.0,
            "beta": 1.5,
        },
        "label": "FeatureSize Vs C Over A Distributions",
    },
    "neighbours": {
        "type": "lognormal",
        "default_keys": {
            "average": 2.0,
            "stddev": 0.5,
        },
        "label": "FeatureSize Vs Neighbors Distributions",
    },
}
DISTRIBUTIONS_TYPE_LABELS = {
    "lognormal": "Log Normal Distribution",
    "beta": "Beta Distribution",
}
DISTRIBUTIONS_KEY_LABELS = {
    "alpha": "Alpha",
    "beta": "Beta",
    "average": "Average",
    "stddev": "Standard Deviation",
}
PRESETS_TYPE_KEYS = {
    "primary_equiaxed": {
        "type",
    },
    "primary_rolled": {
        "type",
        "A_axis_length",
        "B_axis_length",
        "C_axis_length",
    },
    "precipitate_equiaxed": {
        "type",
    },
    "precipitate_rolled": {
        "type",
        "A_axis_length",
        "B_axis_length",
        "C_axis_length",
    },
}
REQUIRED_PHASE_AXIS_ODF_KEYS = {"orientations"}
ALLOWED_PHASE_AXIS_ODF_KEYS = REQUIRED_PHASE_AXIS_ODF_KEYS | {"weights", "sigmas"}
REQUIRED_PHASE_ODF_KEYS = set()  # presets can be specified instead of orientations
ALLOWED_PHASE_ODF_KEYS = ALLOWED_PHASE_AXIS_ODF_KEYS | {"presets"}
DEFAULT_ODF_WEIGHT = 500_000
DEFAULT_ODF_SIGMA = 2

DEFAULT_AXIS_ODF_WEIGHT = DEFAULT_ODF_WEIGHT
DEFAULT_AXIS_ODF_SIGMA = DEFAULT_ODF_SIGMA

ODF_CUBIC_PRESETS = {
    "cube": (0, 0, 0),
    "goss": (0, 45, 0),
    "brass": (35, 45, 0),
    "copper": (90, 35, 45),
    "s": (59, 37, 63),
    "s1": (55, 30, 65),
    "s2": (45, 35, 65),
    "rc(rd1)": (0, 20, 0),
    "rc(rd2)": (0, 35, 0),
    "rc(nd1)": (20, 0, 0),
    "rc(nd2)": (35, 0, 0),
    "p": (70, 45, 0),
    "q": (55, 20, 0),
    "r": (55, 75, 25),
}


def generate_volume_element_statistics(
    path: str | Path,
    grid_size: list[int],
    resolution: list[float] | None,
    size: list[int],
    origin: list[float] | None,
    periodic: bool,
    phase_statistics: list[dict],
    precipitates: bool,
    orientations: Orientations | None,
):
    """'path' is the file path for 'pipeline.json'"""

    if orientations is not None:
        # convert to old-matflow format:
        orientations_ = _convert_orientations_to_old_matflow_format(orientations)
    else:
        orientations_ = None

    if resolution is None:
        resolution = [i / j for i, j in zip(size, grid_size)]

    if origin is None:
        origin = [0, 0, 0]

    vol_frac_sum = 0.0
    stats_JSON = []
    for phase_idx, phase_stats in enumerate(phase_statistics):
        # Validation:

        err_msg = f"Problem with `phase_statistics` index {phase_idx}: "

        phase_type = phase_stats["type"].lower()
        if phase_type not in ALLOWED_PHASE_TYPES:
            raise ValueError(f'{err_msg}`type` "{phase_stats["type"]}" not allowed.')

        given_keys = set(phase_stats.keys())
        miss_keys = REQUIRED_PHASE_KEYS[phase_type] - given_keys
        bad_keys = given_keys - ALLOWED_PHASE_KEYS[phase_type]
        if miss_keys:
            raise ValueError(
                f'{err_msg}Missing keys: {", ".join([f"{i}" for i in miss_keys])}'
            )
        if bad_keys:
            raise ValueError(
                f'{err_msg}Unknown keys: {", ".join([f"{i}" for i in bad_keys])}'
            )

        size_dist = phase_stats["size_distribution"]
        given_size_keys = set(size_dist.keys())
        miss_size_keys = REQUIRED_PHASE_SIZE_DIST_KEYS - given_size_keys
        bad_size_keys = given_size_keys - ALLOWED_PHASE_SIZE_DIST_KEYS
        if miss_size_keys:
            raise ValueError(
                f"{err_msg}Missing `size_distribution` keys: "
                f'{", ".join([f"{i}" for i in miss_size_keys])}'
            )
        if bad_size_keys:
            raise ValueError(
                f"{err_msg}Unknown `size_distribution` keys: "
                f'{", ".join([f"{i}" for i in bad_size_keys])}'
            )
        num_bins = size_dist.get("num_bins")
        bin_step_size = size_dist.get("bin_step_size")
        if sum([i is None for i in (num_bins, bin_step_size)]) != 1:
            raise ValueError(
                f'{err_msg}Specify exactly one of `num_bins` (given as "{num_bins}") '
                f'and `bin_step_size` (given as "{bin_step_size}").'
            )

        if phase_type == "precipitate":
            RDF = phase_stats["radial_distribution_function"]
            given_RDF_keys = set(RDF.keys())
            miss_RDF_keys = ALLOWED_PRECIP_RDF_KEYS - given_RDF_keys
            bad_RDF_keys = given_RDF_keys - ALLOWED_PRECIP_RDF_KEYS

            if miss_RDF_keys:
                raise ValueError(
                    f"{err_msg}Missing `radial_distribution_function` keys: "
                    f'{", ".join([f"{i}" for i in miss_RDF_keys])}'
                )
            if bad_RDF_keys:
                raise ValueError(
                    f"{err_msg}Unknown `radial_distribution_function` keys: "
                    f'{", ".join([f"{i}" for i in bad_RDF_keys])}'
                )

        phase_i_CS = phase_stats["crystal_structure"]
        if phase_i_CS not in ALLOWED_CRYSTAL_STRUCTURES:
            raise ValueError(
                f'{err_msg}`crystal_structure` value "{phase_i_CS}" unknown. '
                f"Must be one of: "
                f'{", ".join([f"{i}" for i in ALLOWED_CRYSTAL_STRUCTURES])}'
            )

        preset = phase_stats.get("preset_statistics_model")
        if preset:
            given_preset_keys = set(preset.keys())
            preset_type = preset.get("type")
            if not preset_type:
                raise ValueError(
                    f"{err_msg}Missing `preset_statistics_model` key: " f'"type".'
                )
            miss_preset_keys = PRESETS_TYPE_KEYS[preset_type] - given_preset_keys
            bad_preset_keys = given_preset_keys - PRESETS_TYPE_KEYS[preset_type]

            if miss_preset_keys:
                raise ValueError(
                    f"{err_msg}Missing `preset_statistics_model` keys: "
                    f'{", ".join([f"{i}" for i in miss_preset_keys])}'
                )
            if bad_preset_keys:
                raise ValueError(
                    f"{err_msg}Unknown `preset_statistics_model` keys: "
                    f'{", ".join([f"{i}" for i in bad_preset_keys])}'
                )

            if "rolled" in preset_type:
                # check: A >= B >= C
                if not (
                    preset["A_axis_length"]
                    >= preset["B_axis_length"]
                    >= preset["C_axis_length"]
                ):
                    raise ValueError(
                        f"{err_msg}The following condition must be true: "
                        f"`A_axis_length >= B_axis_length >= C_axis_length`, but these "
                        f'are, respectively: {preset["A_axis_length"]}, '
                        f'{preset["B_axis_length"]}, {preset["C_axis_length"]}.'
                    )

        # Sum given volume fractions:
        vol_frac_sum += phase_stats["volume_fraction"]

        log_mean = size_dist.get("ESD_log_mean")
        mean = size_dist.get("ESD_mean")
        if sum([i is None for i in (log_mean, mean)]) != 1:
            raise ValueError(
                f"{err_msg}Specify exactly one of `ESD_log_mean` (given as "
                f'"{log_mean}") and `ESD_mean` (given as "{mean}").'
            )

        sigma = size_dist["ESD_log_stddev"]
        if log_mean is None:
            # expected value (mean) of the variable's natural log
            log_mean = np.log(mean) - (sigma**2 / 2)

        sigma_min = size_dist.get("ESD_log_stddev_min_cut_off", SIGMA_MIN_DEFAULT)
        sigma_max = size_dist.get("ESD_log_stddev_max_cut_off", SIGMA_MAX_DEFAULT)
        min_feat_ESD = np.exp(log_mean - (sigma_min * sigma))
        max_feat_ESD = np.exp(log_mean + (sigma_max * sigma))

        if bin_step_size is not None:
            bins = np.arange(min_feat_ESD, max_feat_ESD, bin_step_size)
            num_bins = len(bins)
        else:
            bin_step_size = (max_feat_ESD - min_feat_ESD) / num_bins
            bins = np.linspace(min_feat_ESD, max_feat_ESD, num_bins, endpoint=False)

        feat_diam_info = [bin_step_size, max_feat_ESD, min_feat_ESD]

        # Validate other distributions after sorting out number of bins:
        all_dists = {}
        for dist_key, dist_info in DISTRIBUTIONS_MAP.items():
            dist = size_dist.get(dist_key)
            if not dist:
                if not preset:
                    dist = copy.deepcopy(dist_info["default_keys"])
                else:
                    continue
            else:
                if dist_key == "neighbours" and phase_type == "precipitate":
                    warnings.warn(
                        f"{err_msg}`neighbours` distribution not allowed with "
                        f'"precipitate" phase type; ignoring.'
                    )
                    continue

            required_dist_keys = set(dist_info["default_keys"].keys())
            given_dist_keys = set(dist.keys())

            miss_dist_keys = required_dist_keys - given_dist_keys
            bad_dist_keys = given_dist_keys - required_dist_keys
            if miss_dist_keys:
                raise ValueError(
                    f"{err_msg}Missing `{dist_key}` keys: "
                    f'{", ".join([f"{i}" for i in miss_dist_keys])}'
                )
            if bad_dist_keys:
                raise ValueError(
                    f"{err_msg}Unknown `{dist_key}` keys: "
                    f'{", ".join([f"{i}" for i in bad_dist_keys])}'
                )

            # Match number of distributions to number of bins:
            for dist_param in required_dist_keys:  # i.e. "alpha" and "beta" for beta dist
                dist_param_val = dist[dist_param]

                if isinstance(dist_param_val, np.ndarray):
                    dist_param_val = dist_param_val.tolist()

                if not isinstance(dist_param_val, list):
                    dist_param_val = [dist_param_val]

                if len(dist_param_val) == 1:
                    dist_param_val = dist_param_val * num_bins

                elif len(dist_param_val) != num_bins:
                    raise ValueError(
                        f'{err_msg}Distribution `{dist_key}` key "{dist_param}" must '
                        f"have length one, or length equal to the number of size "
                        f"distribution bins, which is {num_bins}, but in fact has "
                        f"length {len(dist_param_val)}."
                    )
                dist[dist_param] = dist_param_val

            all_dists.update({dist_key: dist})

        # ODF:
        ODF_weights = {}
        axis_ODF_weights = {}
        ODF = phase_stats.get("ODF")
        axis_ODF = phase_stats.get("axis_ODF")

        if ODF or (phase_idx == 0 and orientations_ is not None):
            if not ODF:
                ODF = {}
            given_ODF_keys = set(ODF.keys())
            miss_ODF_keys = REQUIRED_PHASE_ODF_KEYS - given_ODF_keys
            bad_ODF_keys = given_ODF_keys - ALLOWED_PHASE_ODF_KEYS
            if miss_ODF_keys:
                raise ValueError(
                    f"{err_msg}Missing `ODF` keys: "
                    f'{", ".join([f"{i}" for i in miss_ODF_keys])}'
                )
            if bad_ODF_keys:
                raise ValueError(
                    f"{err_msg}Unknown `ODF` keys: "
                    f'{", ".join([f"{i}" for i in bad_ODF_keys])}'
                )

            ODF_presets = ODF.get("presets")

            if phase_idx == 0 and orientations_ is not None:
                # ALlow importing orientations only for the first phase:

                if ODF_presets:
                    warnings.warn(
                        f"{err_msg}Using locally defined ODF presets; not "
                        f"using `orientations` from a previous task."
                    )

                elif "orientations" in ODF:
                    warnings.warn(
                        f"{err_msg}Using locally defined `orientations`, not "
                        f"those from a previous task!"
                    )

                else:
                    ODF["orientations"] = orientations_

            if ODF_presets:
                if any([ODF.get(i) is not None for i in ALLOWED_PHASE_AXIS_ODF_KEYS]):
                    raise ValueError(
                        f"{err_msg}Specify either `presets` or `orientations` (and "
                        f"`sigmas and `weights)."
                    )
                preset_eulers = []
                preset_weights = []
                preset_sigmas = []
                for ODF_preset_idx, ODF_preset in enumerate(ODF_presets):
                    if (
                        "name" not in ODF_preset
                        or ODF_preset["name"].lower() not in ODF_CUBIC_PRESETS
                    ):
                        raise ValueError(
                            f"{err_msg}Specify `name` for ODF preset index "
                            f"{ODF_preset_idx}; one of: "
                            f'{", ".join([f"{i}" for i in ODF_CUBIC_PRESETS.keys()])}'
                        )
                    preset_eulers.append(ODF_CUBIC_PRESETS[ODF_preset["name"].lower()])
                    preset_weights.append(ODF_preset.get("weight", DEFAULT_ODF_WEIGHT))
                    preset_sigmas.append(ODF_preset.get("sigma", DEFAULT_ODF_SIGMA))

                ODF["sigmas"] = preset_sigmas
                ODF["weights"] = preset_weights
                ODF["orientations"] = _process_dream3D_euler_angles(
                    np.array(preset_eulers),
                    degrees=True,
                )

            oris = validate_orientations(ODF["orientations"])  # now as quaternions

            # Convert unit-cell alignment to x//a, as used by Dream.3D:
            if phase_i_CS == "hexagonal":
                if oris["unit_cell_alignment"].get("y") == "b":
                    hex_transform_quat = axang2quat(
                        oris["P"] * np.array([0, 0, 1]), np.pi / 6
                    )
                    for ori_idx, ori_i in enumerate(oris["quaternions"]):
                        oris["quaternions"][ori_idx] = multiply_quaternions(
                            q1=hex_transform_quat,
                            q2=ori_i,
                            P=oris["P"],
                        )
                elif oris["unit_cell_alignment"].get("x") != "a":
                    NotImplementedError(
                        f"Cannot convert from the following specified unit cell "
                        f"alignment to Dream3D-compatible unit cell alignment (x//a): "
                        f'{oris["unit_cell_alignment"]}'
                    )

            num_oris = oris["quaternions"].shape[0]

            # Add defaults:
            if "weights" not in ODF:
                ODF["weights"] = DEFAULT_ODF_WEIGHT
            if "sigmas" not in ODF:
                ODF["sigmas"] = DEFAULT_ODF_SIGMA

            for i in ("weights", "sigmas"):
                val = ODF[i]

                if isinstance(val, np.ndarray):
                    dist_param_val = val.tolist()

                if not isinstance(val, list):
                    val = [val]

                if len(val) == 1:
                    val = val * num_oris

                elif len(val) != num_oris:
                    raise ValueError(
                        f'{err_msg}ODF key "{i}" must have length one, or length equal '
                        f"to the number of ODF orientations, which is {num_oris}, but "
                        f"in fact has length {len(val)}."
                    )
                ODF[i] = val

            # Convert to Euler angles for Dream3D:
            oris_euler = _quat2euler(oris["quaternions"], degrees=False, P=oris["P"])

            ODF_weights = {
                "Euler 1": oris_euler[:, 0].tolist(),
                "Euler 2": oris_euler[:, 1].tolist(),
                "Euler 3": oris_euler[:, 2].tolist(),
                "Sigma": ODF["sigmas"],
                "Weight": ODF["weights"],
            }

        if axis_ODF:
            given_axis_ODF_keys = set(axis_ODF.keys())
            miss_axis_ODF_keys = REQUIRED_PHASE_AXIS_ODF_KEYS - given_axis_ODF_keys
            bad_axis_ODF_keys = given_axis_ODF_keys - ALLOWED_PHASE_AXIS_ODF_KEYS
            if miss_axis_ODF_keys:
                raise ValueError(
                    f"{err_msg}Missing `axis_ODF` keys: "
                    f'{", ".join([f"{i}" for i in miss_axis_ODF_keys])}'
                )
            if bad_axis_ODF_keys:
                raise ValueError(
                    f"{err_msg}Unknown `axis_ODF` keys: "
                    f'{", ".join([f"{i}" for i in bad_axis_ODF_keys])}'
                )

            axis_oris = validate_orientations(
                axis_ODF["orientations"]
            )  # now as quaternions

            # Convert unit-cell alignment to x//a, as used by Dream.3D:
            if phase_i_CS == "hexagonal":
                if axis_oris["unit_cell_alignment"].get("y") == "b":
                    hex_transform_quat = axang2quat(
                        axis_oris["P"] * np.array([0, 0, 1]), np.pi / 6
                    )
                    for ori_idx, ori_i in enumerate(axis_oris["quaternions"]):
                        axis_oris["quaternions"][ori_idx] = multiply_quaternions(
                            q1=hex_transform_quat,
                            q2=ori_i,
                            P=axis_oris["P"],
                        )
                elif axis_oris["unit_cell_alignment"].get("x") != "a":
                    # FIXME: missing raise
                    NotImplementedError(
                        f"Cannot convert from the following specified unit cell "
                        f"alignment to Dream3D-compatible unit cell alignment (x//a): "
                        f'{axis_oris["unit_cell_alignment"]}'
                    )

            num_oris = axis_oris["quaternions"].shape[0]

            # Add defaults:
            if "weights" not in axis_ODF:
                axis_ODF["weights"] = DEFAULT_AXIS_ODF_WEIGHT
            if "sigmas" not in axis_ODF:
                axis_ODF["sigmas"] = DEFAULT_AXIS_ODF_SIGMA

            for i in ("weights", "sigmas"):
                val = axis_ODF[i]

                if isinstance(val, np.ndarray):
                    dist_param_val = val.tolist()

                if not isinstance(val, list):
                    val = [val]

                if len(val) == 1:
                    val = val * num_oris

                elif len(val) != num_oris:
                    raise ValueError(
                        f'{err_msg}axis_ODF key "{i}" must have length one, or length '
                        f"equal to the number of axis_ODF orientations, which is "
                        f"{num_oris}, but in fact has length {len(val)}."
                    )
                axis_ODF[i] = val

            # Convert to Euler angles for Dream3D:
            axis_oris_euler = _quat2euler(
                axis_oris["quaternions"], degrees=False, P=axis_oris["P"]
            )

            axis_ODF_weights = {
                "Euler 1": axis_oris_euler[:, 0].tolist(),
                "Euler 2": axis_oris_euler[:, 1].tolist(),
                "Euler 3": axis_oris_euler[:, 2].tolist(),
                "Sigma": axis_ODF["sigmas"],
                "Weight": axis_ODF["weights"],
            }

        stats_JSON_i = {
            "AxisODF-Weights": axis_ODF_weights,
            "Bin Count": num_bins,
            "BinNumber": bins.tolist(),
            "BoundaryArea": 0,
            "Crystal Symmetry": ALLOWED_CRYSTAL_STRUCTURES[phase_i_CS],
            "FeatureSize Distribution": {
                "Average": log_mean,
                "Standard Deviation": sigma,
            },
            "Feature_Diameter_Info": feat_diam_info,
            "MDF-Weights": {},
            "ODF-Weights": ODF_weights,
            "Name": phase_stats["name"],
            "PhaseFraction": phase_stats["volume_fraction"],
            "PhaseType": phase_stats["type"].title(),
        }

        # Generate dists from `preset_statistics_model`:
        if preset:
            if "omega3" not in all_dists:
                omega3_dist = _generate_omega3_dist_from_preset(num_bins)
                all_dists.update({"omega3": omega3_dist})

            if "c/a" not in all_dists:
                c_a_aspect_ratio = preset["A_axis_length"] / preset["C_axis_length"]
                c_a_dist = _generate_shape_dist_from_preset(
                    num_bins,
                    c_a_aspect_ratio,
                    preset_type,
                )
                all_dists.update({"c/a": c_a_dist})

            if "b/a" not in all_dists:
                b_a_aspect_ratio = preset["A_axis_length"] / preset["B_axis_length"]
                b_a_dist = _generate_shape_dist_from_preset(
                    num_bins,
                    b_a_aspect_ratio,
                    preset_type,
                )
                all_dists.update({"b/a": b_a_dist})

            if phase_type == "primary":
                if "neighbours" not in all_dists:
                    neigh_dist = _generate_neighbour_dist_from_preset(
                        num_bins,
                        preset_type,
                    )
                    all_dists.update({"neighbours": neigh_dist})

        # Coerce distributions into format expected in the JSON:
        for dist_key, dist in all_dists.items():
            dist_info = DISTRIBUTIONS_MAP[dist_key]
            stats_JSON_i.update(
                {
                    dist_info["label"]: {
                        **{DISTRIBUTIONS_KEY_LABELS[k]: v for k, v in dist.items()},
                        "Distribution Type": DISTRIBUTIONS_TYPE_LABELS[dist_info["type"]],
                    }
                }
            )

        if phase_stats["type"] == "precipitate":
            stats_JSON_i.update(
                {
                    "Precipitate Boundary Fraction": phase_stats[
                        "number_fraction_on_boundary"
                    ],
                    "Radial Distribution Function": {
                        "Bin Count": RDF["num_bins"],
                        "BoxDims": np.array(RDF["box_size"]).tolist(),
                        "BoxRes": [  # TODO: how is this calculated?
                            0.1,
                            0.1,
                            0.1,
                        ],
                        "Max": RDF["max_distance"],
                        "Min": RDF["min_distance"],
                    },
                }
            )

        stats_JSON.append(stats_JSON_i)

    if not np.isclose(vol_frac_sum, 1.0):
        raise ValueError(
            f"Sum of `volume_fraction`s over all phases must sum to 1.0, "
            f"but in fact sum to: {vol_frac_sum}"
        )

    stats_data_array = {
        "Name": "Statistics",
        "Phase Count": len(stats_JSON) + 1,  # Don't know why this needs to be +1
    }
    for idx, i in enumerate(stats_JSON, start=1):
        stats_data_array.update({str(idx): i})

    if precipitates:
        precip_inp_file = str(Path(path).parent.joinpath("precipitates.txt"))
    else:
        precip_inp_file = ""

    pipeline = {
        "0": {
            "CellEnsembleAttributeMatrixName": "CellEnsembleData",
            "CrystalStructuresArrayName": "CrystalStructures",
            "Filter_Enabled": True,
            "Filter_Human_Label": "StatsGenerator",
            "Filter_Name": "StatsGeneratorFilter",
            "Filter_Uuid": "{f642e217-4722-5dd8-9df9-cee71e7b26ba}",
            "PhaseNamesArrayName": "PhaseName",
            "PhaseTypesArrayName": "PhaseTypes",
            "StatsDataArray": stats_data_array,
            "StatsDataArrayName": "Statistics",
            "StatsGeneratorDataContainerName": "StatsGeneratorDataContainer",
        },
        "1": {
            # TODO: fix this
            "BoxDimensions": (
                "X Range: 0 to 2 (Delta: 2)\n"
                "Y Range: 0 to 256 (Delta: 256)\n"
                "Z Range: 0 to 256 (Delta: 256)"
            ),
            "CellAttributeMatrixName": "CellData",
            "DataContainerName": "SyntheticVolumeDataContainer",
            "Dimensions": {"x": grid_size[0], "y": grid_size[1], "z": grid_size[2]},
            "EnsembleAttributeMatrixName": "CellEnsembleData",
            "EstimateNumberOfFeatures": 0,
            "EstimatedPrimaryFeatures": "",
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Initialize Synthetic Volume",
            "Filter_Name": "InitializeSyntheticVolume",
            "Filter_Uuid": "{c2ae366b-251f-5dbd-9d70-d790376c0c0d}",
            "InputPhaseTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputStatsArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "Statistics",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "Origin": {"x": origin[0], "y": origin[1], "z": origin[2]},
            "Resolution": {"x": resolution[0], "y": resolution[1], "z": resolution[2]},
        },
        "2": {
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Establish Shape Types",
            "Filter_Name": "EstablishShapeTypes",
            "Filter_Uuid": "{4edbbd35-a96b-5ff1-984a-153d733e2abb}",
            "InputPhaseTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "ShapeTypeData": [999, 0, 0],
            "ShapeTypesArrayName": "ShapeTypes",
        },
        "3": {
            "CellPhasesArrayName": "Phases",
            "FeatureGeneration": 0,
            "FeatureIdsArrayName": "FeatureIds",
            "FeatureInputFile": "",
            "FeaturePhasesArrayName": "Phases",
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Pack Primary Phases",
            "Filter_Name": "PackPrimaryPhases",
            "Filter_Uuid": "{84305312-0d10-50ca-b89a-fda17a353cc9}",
            "InputPhaseNamesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseName",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputPhaseTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputShapeTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "ShapeTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputStatsArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "Statistics",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "MaskArrayPath": {
                "Attribute Matrix Name": "",
                "Data Array Name": "",
                "Data Container Name": "",
            },
            "NewAttributeMatrixPath": {
                "Attribute Matrix Name": "Synthetic Shape Parameters (Primary Phase)",
                "Data Array Name": "",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "NumFeaturesArrayName": "NumFeatures",
            "OutputCellAttributeMatrixPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "OutputCellEnsembleAttributeMatrixName": "CellEnsembleData",
            "OutputCellFeatureAttributeMatrixName": "Grain Data",
            "PeriodicBoundaries": int(periodic),
            "SaveGeometricDescriptions": 0,
            "SelectedAttributeMatrixPath": {
                "Attribute Matrix Name": "",
                "Data Array Name": "",
                "Data Container Name": "",
            },
            "UseMask": 0,
        },
        "4": {
            "BoundaryCellsArrayName": "BoundaryCells",
            "FeatureIdsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "FeatureIds",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Find Boundary Cells (Image)",
            "Filter_Name": "FindBoundaryCells",
            "Filter_Uuid": "{8a1106d4-c67f-5e09-a02a-b2e9b99d031e}",
            "IgnoreFeatureZero": 1,
            "IncludeVolumeBoundary": 0,
        },
        "5": {
            "BoundaryCellsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "BoundaryCells",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "CellPhasesArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "Phases",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FeatureGeneration": 1 if precipitates else 0,  # bug? should be opposite?
            "FeatureIdsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "FeatureIds",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FeaturePhasesArrayPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "Phases",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Insert Precipitate Phases",
            "Filter_Name": "InsertPrecipitatePhases",
            "Filter_Uuid": "{1e552e0c-53bb-5ae1-bd1c-c7a6590f9328}",
            "InputPhaseTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputShapeTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "ShapeTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "InputStatsArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "Statistics",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "MaskArrayPath": {
                "Attribute Matrix Name": "",
                "Data Array Name": "",
                "Data Container Name": "",
            },
            "MatchRDF": 0,
            "NewAttributeMatrixPath": {
                "Attribute Matrix Name": "Synthetic Shape Parameters (Precipitate)",
                "Data Array Name": "",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "NumFeaturesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "NumFeatures",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "PeriodicBoundaries": int(periodic),
            "PrecipInputFile": precip_inp_file,
            "SaveGeometricDescriptions": 0,
            "SelectedAttributeMatrixPath": {
                "Attribute Matrix Name": "",
                "Data Array Name": "",
                "Data Container Name": "",
            },
            "UseMask": 0,
        },
        "6": {
            "BoundaryCellsArrayName": "BoundaryCells",
            "CellFeatureAttributeMatrixPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FeatureIdsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "FeatureIds",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Find Feature Neighbors",
            "Filter_Name": "FindNeighbors",
            "Filter_Uuid": "{97cf66f8-7a9b-5ec2-83eb-f8c4c8a17bac}",
            "NeighborListArrayName": "NeighborList",
            "NumNeighborsArrayName": "NumNeighbors",
            "SharedSurfaceAreaListArrayName": "SharedSurfaceAreaList",
            "StoreBoundaryCells": 0,
            "StoreSurfaceFeatures": 1,
            "SurfaceFeaturesArrayName": "SurfaceFeatures",
        },
        "7": {
            "AvgQuatsArrayName": "AvgQuats",
            "CellEulerAnglesArrayName": "EulerAngles",
            "CrystalStructuresArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "CrystalStructures",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "FeatureEulerAnglesArrayName": "EulerAngles",
            "FeatureIdsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "FeatureIds",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FeaturePhasesArrayPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "Phases",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Match Crystallography",
            "Filter_Name": "MatchCrystallography",
            "Filter_Uuid": "{7bfb6e4a-6075-56da-8006-b262d99dff30}",
            "InputStatsArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "Statistics",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "MaxIterations": 100000,
            "NeighborListArrayPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "NeighborList",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "NumFeaturesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "NumFeatures",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "PhaseTypesArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "PhaseTypes",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "SharedSurfaceAreaListArrayPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "SharedSurfaceAreaList",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "SurfaceFeaturesArrayPath": {
                "Attribute Matrix Name": "Grain Data",
                "Data Array Name": "SurfaceFeatures",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "VolumesArrayName": "Volumes",
        },
        "8": {
            "CellEulerAnglesArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "EulerAngles",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "CellIPFColorsArrayName": "IPFColor",
            "CellPhasesArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "Phases",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "CrystalStructuresArrayPath": {
                "Attribute Matrix Name": "CellEnsembleData",
                "Data Array Name": "CrystalStructures",
                "Data Container Name": "StatsGeneratorDataContainer",
            },
            "FilterVersion": "6.5.141",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Generate IPF Colors",
            "Filter_Name": "GenerateIPFColors",
            "Filter_Uuid": "{a50e6532-8075-5de5-ab63-945feb0de7f7}",
            "GoodVoxelsArrayPath": {
                "Attribute Matrix Name": "CellData",
                "Data Array Name": "",
                "Data Container Name": "SyntheticVolumeDataContainer",
            },
            "ReferenceDir": {"x": 0, "y": 0, "z": 1},
            "UseGoodVoxels": 0,
        },
        "9": {
            "FilterVersion": "1.2.675",
            "Filter_Enabled": True,
            "Filter_Human_Label": "Write DREAM.3D Data File",
            "Filter_Name": "DataContainerWriter",
            "Filter_Uuid": "{3fcd4c43-9d75-5b86-aad4-4441bc914f37}",
            "OutputFile": (
                f"{str(Path(path).absolute().parent.joinpath('pipeline.dream3d'))}"
            ),
            "WriteTimeSeries": 0,
            "WriteXdmfFile": 1,
        },
        "PipelineBuilder": {
            "Name": "RVE from precipitate statistics",
            "Number_Filters": 10,
            "Version": 6,
        },
    }

    with Path(path).open("w") as fh:
        json.dump(pipeline, fh, indent=4)


def _convert_orientations_to_old_matflow_format(orientations: Orientations):
    # see `LatticeDirection` enum:
    align_lookup = {
        "A": "a",
        "B": "b",
        "C": "c",
        "A_STAR": "a*",
        "B_STAR": "b*",
        "C_STAR": "c*",
    }
    unit_cell_alignment = {
        "x": align_lookup[orientations.unit_cell_alignment.x.name],
        "y": align_lookup[orientations.unit_cell_alignment.y.name],
        "z": align_lookup[orientations.unit_cell_alignment.z.name],
    }
    type_lookup = {
        "QUATERNION": "quat",
        "EULER": "euler",
    }
    type_ = type_lookup[orientations.representation.type.name]
    oris = {
        "type": type_,
        "unit_cell_alignment": unit_cell_alignment,
    }

    if type_ == "quat":
        quat_order = orientations.representation.quat_order.name.lower().replace("_", "-")
        oris["quaternions"] = np.array(orientations.data)
        oris["quat_component_ordering"] = quat_order
    elif type_ == "euler":
        oris["euler_angles"] = np.array(orientations.data)
        oris["euler_degrees"] = orientations.representation.euler_is_degrees

    return oris


## These next two functions are from matflow.matflow_dream3d.utilities
# https://github.com/LightForm-group/matflow-dream3d/blob/3c73bd043b8e80bdc17af434e9e89a1660cffc2d/matflow_dream3d/utilities.py
def _quat2euler(quats: NDArray, degrees: bool = False, P: int = 1) -> NDArray:
    """Convert quaternions to Bunge-convention Euler angles.

    Parameters
    ----------
    quats : ndarray of shape (N, 4) of float
        Array of N row four-vectors of unit quaternions.
    degrees : bool, optional
        If True, `euler_angles` are returned in degrees, rather than radians.

    P : int, optional
        The "P" constant, either +1 or -1, as defined within [1].

    Returns
    -------
    euler_angles : ndarray of shape (N, 3) of float
        Array of N row three-vectors of Euler angles, specified as proper Euler angles in
        the Bunge convention (rotations are about Z, new X, new new Z).

    Notes
    -----
    Conversion of quaternions to Bunge Euler angles due to Ref. [1].

    References
    ----------
    [1] Rowenhorst, D, A D Rollett, G S Rohrer, M Groeber, M Jackson,
        P J Konijnenberg, and M De Graef. "Consistent Representations
        of and Conversions between 3D Rotations". Modelling and Simulation
        in Materials Science and Engineering 23, no. 8 (1 December 2015):
        083501. https://doi.org/10.1088/0965-0393/23/8/083501.

    """

    num_oris = quats.shape[0]
    euler_angles = np.zeros((num_oris, 3))

    q0, q1, q2, q3 = quats.T

    q03 = q0**2 + q3**2
    q12 = q1**2 + q2**2
    chi = np.sqrt(q03 * q12)

    chi_zero_idx = np.isclose(chi, 0)
    q12_zero_idx = np.isclose(q12, 0)
    q03_zero_idx = np.isclose(q03, 0)

    # Three cases are distinguished:
    idx_A = np.logical_and(chi_zero_idx, q12_zero_idx)
    idx_B = np.logical_and(chi_zero_idx, q03_zero_idx)
    idx_C = np.logical_not(chi_zero_idx)

    q0A, q3A = q0[idx_A], q3[idx_A]
    q1B, q2B = q1[idx_B], q2[idx_B]
    q0C, q1C, q2C, q3C, chiC = q0[idx_C], q1[idx_C], q2[idx_C], q3[idx_C], chi[idx_C]

    q03C = q03[idx_C]
    q12C = q12[idx_C]

    # Case 1
    euler_angles[idx_A, 0] = np.arctan2(-2 * P * q0A * q3A, q0A**2 - q3A**2)

    # Case 2
    euler_angles[idx_B, 0] = np.arctan2(2 * q1B * q2B, q1B**2 - q2B**2)
    euler_angles[idx_B, 1] = np.pi

    # Case 3
    euler_angles[idx_C, 0] = np.arctan2(
        (q1C * q3C - P * q0C * q2C) / chiC,
        (-P * q0C * q1C - q2C * q3C) / chiC,
    )
    euler_angles[idx_C, 1] = np.arctan2(2 * chiC, q03C - q12C)
    euler_angles[idx_C, 2] = np.arctan2(
        (P * q0C * q2C + q1C * q3C) / chiC,
        (q2C * q3C - P * q0C * q1C) / chiC,
    )

    euler_angles[euler_angles[:, 0] < 0, 0] += 2 * np.pi
    euler_angles[euler_angles[:, 2] < 0, 2] += 2 * np.pi

    if degrees:
        euler_angles = np.rad2deg(euler_angles)

    return euler_angles


def _process_dream3D_euler_angles(euler_angles: dict, degrees: bool = False) -> dict:
    orientations = {
        "type": "euler",
        "euler_degrees": degrees,
        "euler_angles": euler_angles,
        "unit_cell_alignment": {"x": "a"},
    }
    return orientations


# These next three functions are from
# https://github.com/LightForm-group/matflow-dream3d/blob/3c73bd043b8e80bdc17af434e9e89a1660cffc2d/matflow_dream3d/preset_statistics.py
"""Functions for replicating preset statistics models as implemented in Dream.3D"""


def _generate_omega3_dist_from_preset(num_bins: int) -> dict[str, list[float]]:
    """Replicating: https://github.com/BlueQuartzSoftware/DREAM3D/blob/331c97215bb358321d9f92105a9c812a81fd1c79/Source/Plugins/SyntheticBuilding/SyntheticBuildingFilters/Presets/PrimaryRolledPreset.cpp#L62"""
    alphas = 10.0 + np.random.rand(num_bins)
    betas = 1.5 + (0.5 * np.random.rand(num_bins))
    return {"alpha": alphas.tolist(), "beta": betas.tolist()}


def _generate_shape_dist_from_preset(
    num_bins: int, aspect_ratio: float, preset_type: str
) -> dict[str, list[float]]:
    """Replicating: https://github.com/BlueQuartzSoftware/DREAM3D/blob/331c97215bb358321d9f92105a9c812a81fd1c79/Source/Plugins/SyntheticBuilding/SyntheticBuildingFilters/Presets/PrimaryRolledPreset.cpp#L88"""
    if preset_type in ("primary_rolled", "precipitate_rolled"):
        alphas = 1.1 + (28.9 / aspect_ratio) + np.random.rand(num_bins)
        betas = 30 - (28.9 / aspect_ratio) + np.random.rand(num_bins)
    elif preset_type in ("primary_equiaxed", "precipitate_equiaxed"):
        alphas = 15.0 + np.random.rand(num_bins)
        betas = 1.25 + (0.5 * np.random.rand(num_bins))
    else:
        raise ValueError(f"unsupported preset_type: {preset_type}")
    return {"alpha": alphas.tolist(), "beta": betas.tolist()}


def _generate_neighbour_dist_from_preset(
    num_bins: int, preset_type: str
) -> dict[str, list[float]]:
    """Replicating: https://github.com/BlueQuartzSoftware/DREAM3D/blob/331c97215bb358321d9f92105a9c812a81fd1c79/Source/Plugins/SyntheticBuilding/SyntheticBuildingFilters/Presets/PrimaryRolledPreset.cpp#L140"""
    middlebin = num_bins // 2
    relative_bins = np.arange(num_bins) - middlebin
    if preset_type == "primary_equiaxed":
        mus = np.log(14.0 + 2.0 * relative_bins)
        sigmas = 0.3 - relative_bins / (middlebin * 10)
    elif preset_type == "primary_rolled":
        mus = np.log(8.0 + relative_bins)
        sigmas = 0.3 - relative_bins / (middlebin * 10)
    else:
        raise ValueError(f"unsupported preset_type: {preset_type}")
    return {"average": mus.tolist(), "stddev": sigmas.tolist()}
