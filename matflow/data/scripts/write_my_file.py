from pathlib import Path


def write_my_file(path, p1):
    with Path(path).open("wt") as fp:
        fp.write(str(p1))
