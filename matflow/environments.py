"""
Functions for configuring MatFlow environments.

"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Literal

import matflow as mf

from hpcflow.sdk.submission.schedulers.utils import run_cmd
from hpcflow.sdk.utils.envs import norm_env_setup, get_env_py_exe

if TYPE_CHECKING:
    from hpcflow.sdk.core.environment import Environment


def env_configure_dream3d(
    shell: Literal["bash", "powershell"],
    pipeline_runner_path: str,
    setup_py: str | list[str] | None = None,
    setup_runner: str | list[str] | None = None,
    use_current: bool = True,
) -> Environment:
    """Configure the Dream3D MatFlow environment.

    The Dream3D environment requires:

    1. a `dream_3D_runner` executable that runs the PipelineRunner CLI tool, and
    2. a `python_script` executable that runs the pre and post processing.

    """

    if not Path(pipeline_runner_path).is_file():
        raise ValueError(
            f"The specified Dream3D pipeline runner path is not a file: "
            f"{pipeline_runner_path!r}."
        )

    setup_py = norm_env_setup(setup_py)
    setup_runner = norm_env_setup(setup_runner)
    RUNNER = {
        "bash": str(pipeline_runner_path),
        "powershell": f"& '{pipeline_runner_path}'",
    }
    executables = [
        mf.Executable(
            label="dream_3D_runner",
            instances=[
                mf.ExecutableInstance(
                    command=RUNNER[shell],
                    num_cores=1,
                    parallel_mode=None,
                ),
            ],
        ),
        mf.Executable(
            label="python_script",
            instances=[
                mf.ExecutableInstance(
                    command=(f'{get_env_py_exe(shell)} "<<script_path>>" <<args>>'),
                    num_cores=1,
                    parallel_mode=None,
                ),
            ],
        ),
    ]
    setup = setup_runner + (mf.get_env_setup(shell) if use_current else setup_py)
    return mf.Environment(
        name="dream_3D_env",
        setup=setup,
        executables=executables,
        setup_label="dream3d",
    )


def env_configure_python_all(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    use_current: bool = True,
) -> list[Environment]:
    """
    Configure all of the Python environments, using the same setup.
    """
    return mf.env_configure_python(
        shell=shell,
        setup=setup,
        use_current=use_current,
        names=(
            "damask_parse",
            "sklearn",
            "formable",
            "defdap",
            "gmsh",
            "moose_processing",
        ),
    )


def env_configure_matlab(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    matlab_path: str | None = None,
    matlab_runtime_path: str | None = None,
    mtex_path: str | None = None,
) -> Environment:
    """Configure the MATLAB MatFlow environment.

    Different environment executables are configured depending on what arguments are
    provided:

    1. If `matlab_path` and `mtex_path` are specified, then the `run_mtex`
       executable is configured.
    2. If `mcc_path` and `mtex_path` are specified, then the `compile_mtex` and
       `run_compiled_mtex` executables are configured.
    3. If `matlab_runtime_path` is specified, the `run_precompiled_mtex` executable is
       configured. Note that if `matlab_path` is specified, `matlab_runtime_path` will by
       default be set to the value of `matlab_path`.

    """

    matlab_exe = None
    matlab_mcc = None

    if matlab_path:
        matlab_path_ = Path(matlab_path)

        mcc_ext = ".bat" if shell == "powershell" else ""
        exe_ext = ".exe" if shell == "powershell" else ""

        matlab_exe = matlab_path_.joinpath("bin", f"matlab{exe_ext}")
        matlab_mcc = matlab_path_.joinpath("bin", f"mcc{mcc_ext}")

        matlab_runtime_path = matlab_runtime_path or matlab_path

        if shell != "powershell":
            matlab_exe = matlab_exe.as_posix()
            matlab_mcc = matlab_mcc.as_posix()

    run_mtex_cmd_nt = (
        f"& '{matlab_exe}' -batch \"addpath('<<script_dir>>'); "
        '<<script_name_no_ext>> <<args>>"'
    )
    run_mtex_cmd_posix = dedent(
        f"""\
        MTEX_DIR={mtex_path}
        for dir in $(find ${{MTEX_DIR}} -type d | grep -v -e ".git" -e "@" -e "private"); do MATLABPATH="${{dir}};${{MATLABPATH}}"; done
        export MATLABPATH=${{MATLABPATH}}
        {matlab_exe} -softwareopengl -singleCompThread -batch "addpath('<<script_dir>>'); <<script_name_no_ext>> <<args>>"
        """
    )
    compile_mtex_cmd_nt = (
        f"$mtex_path = '{mtex_path}'\n"
        f'& \'{matlab_mcc}\' -R -singleCompThread -m "<<script_path>>" <<args>> -o matlab_exe -a "$mtex_path/data" -a "$mtex_path/plotting/plotting_tools/colors.mat"'
    )

    compile_mtex_cmd_posix = dedent(
        f"""\
        MTEX_DIR={mtex_path}
        for dir in $(find ${{MTEX_DIR}} -type d | grep -v -e ".git" -e "@" -e "private" -e "data" -e "makeDoc" -e "templates" -e "nfft_openMP" -e "compatibility/")
        do
            MTEX_INCLUDE="-I ${{dir}} ${{MTEX_INCLUDE}}"
        done
        export MTEX_INCLUDE="${{MTEX_INCLUDE}} -a ${{MTEX_DIR}}/data -a ${{MTEX_DIR}}/plotting/plotting_tools/colors.mat"
        {matlab_mcc} -R -singleCompThread -R -softwareopengl -m "<<script_path>>" <<args>> -o matlab_exe ${{MTEX_INCLUDE}}
        """
    )

    run_compiled_mtex_nt = R".\matlab_exe.exe <<args>>"
    run_compiled_mtex_posix = dedent(
        f"""\
        export MATLAB_RUNTIME={matlab_runtime_path}
        ./run_matlab_exe.sh ${{MATLAB_RUNTIME}} <<args>>
        """
    )

    run_precompiled_mtex_nt = "& <<program_path>> <<args>>"
    run_precompiled_mtex_posix = dedent(
        f"""\
        export MATLAB_RUNTIME={matlab_runtime_path}
        <<program_path>> ${{MATLAB_RUNTIME}} <<args>>
        """
    )

    executables = []

    if matlab_path and mtex_path:

        mtex_path_ = Path(mtex_path)

        executables.append(
            mf.Executable(
                label="run_mtex",
                instances=[
                    mf.ExecutableInstance(
                        command=(
                            run_mtex_cmd_nt
                            if shell == "powershell"
                            else run_mtex_cmd_posix
                        ),
                        num_cores=1,
                        parallel_mode=None,
                    ),
                ],
            )
        )

        if matlab_mcc.is_file():
            executables.extend(
                [
                    mf.Executable(
                        label="compile_mtex",
                        instances=[
                            mf.ExecutableInstance(
                                command=(
                                    compile_mtex_cmd_nt
                                    if shell == "powershell"
                                    else compile_mtex_cmd_posix
                                ),
                                num_cores=1,
                                parallel_mode=None,
                            ),
                        ],
                    ),
                    mf.Executable(
                        label="run_compiled_mtex",
                        instances=[
                            mf.ExecutableInstance(
                                command=(
                                    run_compiled_mtex_nt
                                    if shell == "powershell"
                                    else run_compiled_mtex_posix
                                ),
                                num_cores=1,
                                parallel_mode=None,
                            ),
                        ],
                    ),
                ]
            )
        else:
            print(
                f"Not defining the `compile_mtex` executable because the MATLAB compiler "
                f"was not found."
            )

    if matlab_runtime_path:
        executables.append(
            mf.Executable(
                label="run_precompiled_mtex",
                instances=[
                    mf.ExecutableInstance(
                        command=(
                            run_precompiled_mtex_nt
                            if shell == "powershell"
                            else run_precompiled_mtex_posix
                        ),
                        num_cores=1,
                        parallel_mode=None,
                    ),
                ],
            )
        )

    new_env = mf.Environment(
        name="matlab_env",
        setup=setup,
        executables=executables,
        setup_label="matlab",
    )
    return new_env


def env_configure_damask(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    docker_image: str | None = None,
    docker_archive: str | Path | None = None,
    singularity_archive: str | Path | None = None,
    singularity_sif: str | Path | None = None,
    docker_exe: str = "docker",
    singularity_exe: str = "singularity",
):
    """Configure the MatFlow DAMASK environment.

    If passing a path to an archive, the name of the image within the archive can be
    passed via `docker_image`.

    Parameters
    ----------
    docker_image
        Name of the docker image to use.
    docker_archive:
        File path to an archived docker tar file. Use `docker_image` to set the image
        name within the tar (assumed to be "damask").
    singularity_archive
        File path to an archived docker tar file to be converted into a singularity
        sif file to use.
    singularity_sif
        File path to a Singularity sif file to use.
    """

    use_docker = bool(docker_image or docker_archive)
    use_singularity = bool(singularity_sif or singularity_archive)

    if use_docker and use_singularity:
        raise ValueError("Cannot use both singularity and docker!")

    if use_docker:
        if docker_image is None and docker_archive is None:
            raise ValueError(
                f"Provide either the docker image name, or the docker archive file path "
                f"(and optionally the image name within the archive)."
            )

        if docker_archive is not None and docker_image is None:
            # assume image name to be damask:
            docker_image = "damask"

        if docker_archive:
            # load with docker from an tar archive:
            cmd = (docker_exe, "load", "--input", str(docker_archive))
            run_cmd(cmd)

        if use_docker:
            DAMASK_GRID_CMD = {
                "bash": (
                    f"{docker_exe} run --rm --interactive --volume $PWD:/wd --env "
                    f"OMP_NUM_THREADS=$MATFLOW_RUN_NUM_THREADS {docker_image}"
                ),
                "powershell": (
                    f"{docker_exe} run --rm --interactive --volume ${{PWD}}:/wd --env "
                    f"OMP_NUM_THREADS=$MATFLOW_RUN_NUM_THREADS {docker_image}"
                ),
            }
    elif use_singularity:
        if singularity_archive:
            singularity_sif = singularity_sif or "damask.sif"  # i.e. pwd
            cmd = (
                singularity_exe,
                "build",
                singularity_sif,
                f"docker-archive://{singularity_archive}",
            )
            run_cmd(cmd)

        DAMASK_GRID_CMD = {
            "bash": (
                f"{singularity_exe} run -B $PWD:/wd {singularity_sif} --env "
                f"OMP_NUM_THREADS=$MATFLOW_RUN_NUM_THREADS"
            ),
        }

    executables = []
    executables.append(
        mf.Executable(
            label="damask_grid",
            instances=[
                mf.ExecutableInstance(
                    command=DAMASK_GRID_CMD[shell],
                    num_cores={"start": 1, "stop": 100, "step": 1},
                    parallel_mode=None,
                ),
            ],
        )
    )

    new_env = mf.Environment(
        name="damask_env",
        setup=setup,
        executables=executables,
        setup_label="damask",
    )
    return new_env


def env_configure_moose(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    docker_image: str | None = None,
    docker_archive: str | Path | None = None,
    singularity_archive: str | Path | None = None,
    singularity_sif: str | Path | None = None,
    docker_exe: str = "docker",
    singularity_exe: str = "singularity",
):
    """Configure the MatFlow MOOSE (proteus) environment.

    If passing a path to an archive, the name of the image within the archive can be
    passed via `docker_image`.

    Parameters
    ----------
    docker_image
        Name of the docker image to use.
    docker_archive:
        File path to an archived docker tar file. Use `docker_image` to set the image
        name within the tar (assumed to be "proteus").
    singularity_archive
        File path to an archived docker tar file to be converted into a singularity
        sif file to use.
    singularity_sif
        File path to a Singularity sif file to use.
    """

    use_docker = bool(docker_image or docker_archive)
    use_singularity = bool(singularity_sif or singularity_archive)

    if use_docker and use_singularity:
        raise ValueError("Cannot use both singularity and docker!")

    if use_docker:
        if docker_image is None and docker_archive is None:
            raise ValueError(
                f"Provide either the docker image name, or the docker archive file path "
                f"(and optionally the image name within the archive)."
            )

        if docker_archive is not None and docker_image is None:
            # assume image name to be proteus:
            docker_image = "proteus"

        if docker_archive:
            # load with docker from an tar archive:
            cmd = (docker_exe, "load", "--input", str(docker_archive))
            run_cmd(cmd)

        if use_docker:
            PROTEUS_CMD = {
                "bash": (
                    f"{docker_exe} run --rm --interactive --volume $PWD:/wd "
                    f"{docker_image} --n-threads=$MATFLOW_RUN_NUM_THREADS"
                ),
                "powershell": (
                    f"{docker_exe} run --rm --interactive --volume ${{PWD}}:/wd "
                    f"{docker_image} --n-threads=$MATFLOW_RUN_NUM_THREADS"
                ),
            }
    elif use_singularity:
        if singularity_archive:
            singularity_sif = singularity_sif or "proteus.sif"  # i.e. pwd
            cmd = (
                singularity_exe,
                "build",
                singularity_sif,
                f"docker-archive://{singularity_archive}",
            )
            run_cmd(cmd)

        PROTEUS_CMD = {
            "bash": (
                f"{singularity_exe} run -B $PWD:/wd {singularity_sif} "
                f"--n-threads=$MATFLOW_RUN_NUM_THREADS"
            ),
        }

    executables = []
    executables.append(
        mf.Executable(
            label="proteus",
            instances=[
                mf.ExecutableInstance(
                    command=PROTEUS_CMD[shell],
                    num_cores={"start": 1, "stop": 100, "step": 1},
                    parallel_mode=None,
                ),
            ],
        )
    )

    new_env = mf.Environment(
        name="moose_env",
        setup=setup,
        executables=executables,
        setup_label="moose",
    )
    return new_env
