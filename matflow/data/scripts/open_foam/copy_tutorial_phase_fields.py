import re
from pathlib import Path


def _replace_boundary_field(text, boundary_field):
    match = re.search(r"\bboundaryField\s*\{", text)
    if not match:
        raise ValueError("Phase field file does not contain a boundaryField dictionary.")

    brace_start = text.find("{", match.start())
    depth = 0
    brace_end = None
    for idx in range(brace_start, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                brace_end = idx
                break

    if brace_end is None:
        raise ValueError("Phase field boundaryField dictionary is not closed.")

    entries = "\n".join(
        "    {patch_name}\n"
        "    {{\n"
        "        type            {type};\n"
        "    }}".format(**patch)
        for patch in boundary_field
    )
    return text[:brace_start + 1] + "\n" + entries + "\n" + text[brace_end:]


def copy_tutorial_phase_fields(path, root_path, boundary_field):
    source_dir = Path(root_path) / "initial"
    output_dir = path.parent

    phase_files = sorted(source_dir.glob("n.*"))
    if not phase_files:
        raise FileNotFoundError(f"No tutorial phase fields found in {source_dir}.")

    for source in phase_files:
        text = source.read_text()
        updated = _replace_boundary_field(text, boundary_field)
        output_dir.joinpath(source.name).write_text(updated)
