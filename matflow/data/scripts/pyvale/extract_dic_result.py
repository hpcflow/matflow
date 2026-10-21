from pathlib import Path
from natsort import natsorted
import pyvale.dic as dic


def extract_dic_result(pyvale_dic_result_files: list[Path]):
    dicdata = dic.import_2d(
        natsorted(pyvale_dic_result_files), binary=True, layout="matrix"
    )
    return {
        k: getattr(dicdata, k)
        for k in [
            "ss_x",
            "ss_y",
            "u",
            "v",
            "mag",
            "converged",
            "cost",
            "ftol",
            "xtol",
            "niter",
        ]
    }
