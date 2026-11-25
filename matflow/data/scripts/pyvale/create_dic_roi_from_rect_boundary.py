from pathlib import Path
import pyvale.dic as dic
import numpy as np
from PIL import Image


def create_dic_roi_from_rect_boundary(
    reference_image_path: str, crop_dists: dict[str, int] | None = None
):
    ref_image = np.array(Image.open(Path(reference_image_path)))

    crop_dists_default = {
        "left": 0,
        "right": 0,
        "top": 0,
        "bottom": 0,
    }
    if crop_dists is not None:
        crop_dists_default.update(crop_dists)
    crop_dists = crop_dists_default

    roi = dic.RegionOfInterest(ref_image=ref_image)
    roi.rect_boundary(**crop_dists)

    return {"DIC_mask": roi.mask}
