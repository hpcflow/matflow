from pathlib import Path


def write_precipitates_file(path, precipitates):
    if precipitates:
        with Path(path).open("wt") as fp:
            fp.write(str(len(precipitates)) + "\n")
            for i in precipitates:
                fp.write(
                    f"{i['phase_number']} "
                    f"{i['position'][0]:.6f} {i['position'][1]:.6f} {i['position'][2]:.6f} "
                    f"{i['major_semi_axis_length']:.6f} "
                    f"{i['mid_semi_axis_length']:.6f} "
                    f"{i['minor_semi_axis_length']:.6f} "
                    f"{i.get('omega3', 1):.6f} "
                    f"{i['euler_angle'][0]:.6f} "
                    f"{i['euler_angle'][1]:.6f} "
                    f"{i['euler_angle'][2]:.6f}\n"
                )
