"""
Custom encoders and decoders for parameter data.
"""

from collections import defaultdict

from hpcflow.sdk.core.utils import get_relative_path, get_in_container, set_in_container


def _try_import_arviz():
    """Try to import Arviz, a package for Bayesian model analysis."""
    try:
        import arviz

        return arviz
    except ImportError:
        return False


def _zarr_encode_arviz_inference_data(
    obj,
    type_lookup,
    path,
    root_encoder,
    **kwargs,
):
    """Encode to the Zarr store an InferenceData object from the arviz package."""
    type_lookup["arviz.data.inference_data.InferenceData"].append(path)
    return root_encoder(obj.to_dict(), type_lookup=type_lookup, path=path, **kwargs)[
        "data"
    ]


def _zarr_decode_arviz_inference_data(
    obj,
    type_lookup,
    path,
    **kwargs,
):
    """Decode from the Zarr store an InferenceData object from the arviz package."""
    if arviz := _try_import_arviz():
        for dat_path in type_lookup.get("arviz.data.inference_data.InferenceData", []):
            try:
                rel_path = get_relative_path(dat_path, path)
            except ValueError:
                continue

            if rel_path:
                set_in_container(
                    obj, rel_path, arviz.from_dict(**get_in_container(obj, rel_path))
                )
            else:
                obj = arviz.from_dict(**obj)

    return obj


def get_encoders():
    """Get additional app defined encoders."""
    encoders = defaultdict(dict)
    if arviz := _try_import_arviz():
        encoders["zarr"][
            arviz.data.inference_data.InferenceData
        ] = _zarr_encode_arviz_inference_data

    return encoders


def get_decoders():
    """Get additional app defined decoders."""
    decoders = defaultdict(dict)
    if _try_import_arviz():
        decoders["zarr"][
            "arviz.data.inference_data.InferenceData"
        ] = _zarr_decode_arviz_inference_data

    return decoders
