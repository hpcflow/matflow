from pathlib import Path
from natsort import natsorted
import pyvale.dic as dic
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def run_dic(
    reference_image_path: str,
    deformed_image_path: str,
    DIC_mask: np.ndarray | None = None,
    DIC_seed: list[int] | None = None,
    **kwargs
):
    reference_image_path = Path(reference_image_path)
    ref_image = np.array(Image.open(reference_image_path))

    deformed_image_path = Path(deformed_image_path)
    deformed_image_paths = natsorted(
        deformed_image_path.parent.glob(deformed_image_path.name)
    )
    def_images = []
    for deformed_image_path in deformed_image_paths:
        if deformed_image_path == reference_image_path:
            continue
        def_images.append(np.array(Image.open(deformed_image_path)))
    def_images = np.array(def_images)

    if DIC_seed is None:
        DIC_seed = [ref_image.shape[1] // 2, ref_image.shape[0] // 2]

    if DIC_mask is None:
        roi = dic.RegionOfInterest(ref_image=ref_image)
        roi.rect_boundary(left=0, right=0, top=0, bottom=0)
        DIC_mask = roi.mask

    dic_args = {k: v for k, v in kwargs.items() if v is not None}
    dic.calculate_2d(
        reference=ref_image,
        deformed=def_images,
        roi_mask=DIC_mask,
        seed=DIC_seed,
        output_at_end=True,
        output_binary=True,
        output_below_threshold=True,
        **dic_args
    )
