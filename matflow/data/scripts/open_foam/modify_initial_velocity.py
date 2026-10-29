import re
from pathlib import Path


def modify_initial_velocity(path, root_path, peak_velocity, velocity_radius):
    source = Path(root_path) / "initial" / "U"
    text = source.read_text()

    if peak_velocity < 0:
        raise ValueError("peak_velocity must be non-negative; patch directions preserve the tutorial signs.")
    if velocity_radius <= 0:
        raise ValueError("velocity_radius must be positive.")

    radius_pattern = re.compile(r"(scalar radius\s*=)\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?;")
    text, radius_count = radius_pattern.subn(
        lambda match: f"{match.group(1)}{velocity_radius:.12g};",
        text,
    )
    if radius_count == 0:
        raise ValueError("No velocity profile radius declarations found in the tutorial initial/U.")

    peak_pattern = re.compile(
        r"(scalar Peak\s*=)\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?);"
    )

    def replace_peak(match):
        tutorial_peak = float(match.group(2))
        peak = -abs(peak_velocity) if tutorial_peak < 0 else abs(peak_velocity)
        return f"{match.group(1)}{peak:.12g};"

    text, peak_count = peak_pattern.subn(replace_peak, text)
    if peak_count == 0:
        raise ValueError("No velocity profile peak declarations found in the tutorial initial/U.")

    path.write_text(text)
