from pathlib import Path


def dump_group_data(p2, dump_path):
    with Path(dump_path).open("wt") as fh:
        fh.write(str(p2))
    return {}
