import json
import sys
import re
from pathlib import Path

_NUMBER_RE = re.compile(r"\d+")
_VERSION_RE = re.compile(r"(v\d+\.\d+\.\d+((?:a|b|rc).*)?)")


def pad_version(version: str, pad_length: int = 3):
    p = ""
    n: str
    for n in _NUMBER_RE.findall(version):
        p += n.zfill(pad_length)
    if "a" not in version:
        p += "9" * pad_length  # stable versions before pre-releases (with `reverse=True`)
    return p


def write_switcher_json(*args: str):
    url_prefix = args[0] if args else "/"
    if not url_prefix.startswith("/"):
        url_prefix = f"/{url_prefix}"
    if not url_prefix.endswith("/"):
        url_prefix = f"{url_prefix}/"

    docs_dir = Path(__file__).parent.resolve()
    all_vers = sorted(
        (i.name for i in docs_dir.glob("*") if i.is_dir() and not i.is_symlink()),
        key=lambda i: pad_version(i),
        reverse=True,
    )

    vers_switcher = []
    dev_named = False
    stable_named = False
    for idx, vers in enumerate(all_vers):
        is_dev = bool(_VERSION_RE.search(vers).group(1))
        if not is_dev and not stable_named:
            stable_named = True
            name = f"stable ({vers})"
            if idx == 0:
                dev_named = True
                # don't label dev if there is no dev version beyond stable
        elif is_dev and not dev_named:
            dev_named = True
            name = f"dev ({vers})"
        else:
            name = vers

        vers_switcher.append(
            {"name": name, "version": vers.lstrip("v"), "url": f"{url_prefix}{vers}/"}
        )

    with docs_dir.joinpath("switcher.json").open("w") as fh:
        json.dump(vers_switcher, fh, indent=4)
        fh.write("\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    write_switcher_json(*args)
