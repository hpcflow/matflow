from pathlib import Path


def read_my_file(my_file):
    with Path(my_file).open("rt") as fp:
        return fp.read()
