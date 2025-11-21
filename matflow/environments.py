"""
Functions for configuring MatFlow environments.

"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Literal
import sys

import matflow as mf

if TYPE_CHECKING:
    from hpcflow.sdk.core.environment import Environment


def __norm_setup(setup: str | list[str] | None = None):
    if setup is None:
        return []
    if isinstance(setup, str):
        return [setup]
    return setup


def __get_py_exe(shell: Literal["bash", "powershell"]) -> str:
    return {
        "bash": sys.executable,
        "powershell": f"& '{sys.executable}'",
    }[shell]


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

    setup_py = __norm_setup(setup_py)
    setup_runner = __norm_setup(setup_runner)
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
                    command=(f'{__get_py_exe(shell)} "<<script_path>>" <<args>>'),
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


def env_configure_python(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    names: list[str] | None = None,
    use_current: bool = True,
) -> list[Environment]:
    """Configure Python MatFlow environments.

    Parameters
    ----------
    names:
        If specified, also set up these named environments using the same Python
        executable and setup, otherwise just set up the `python_env` environment.
    """
    setup = __norm_setup(setup)
    executables = [
        mf.Executable(
            label="python_script",
            instances=[
                mf.ExecutableInstance(
                    command=(f'{__get_py_exe(shell)} "<<script_path>>" <<args>>'),
                    num_cores=1,
                    parallel_mode=None,
                ),
            ],
        ),
    ]
    setup = mf.get_env_setup(shell) if use_current else setup
    environments = []
    for name in sorted(set(["python", *(names if names else [])])):
        environments.append(
            mf.Environment(
                name=f"{name}_env",
                setup=setup,
                executables=executables,
                setup_label="python",
            )
        )
    return environments


def env_configure_python_all(
    shell: Literal["bash", "powershell"],
    setup: str | list[str] | None = None,
    use_current: bool = True,
) -> list[Environment]:
    """
    Configure all of the Python environments, using the same setup.
    """
    return env_configure_python(
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

    if matlab_path:
        matlab_path_ = Path(matlab_path)
        if not matlab_path_.is_dir():
            raise ValueError(
                "`matlab_path` must be specified as the base directory to the MATLAB "
                "installation."
            )

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

        # must be able to run matlab:
        if not matlab_exe.is_file():
            raise ValueError(f"MATLAB executable does not exist: {matlab_exe!r}.")

        if not mtex_path_.is_dir():
            raise ValueError(f"MTEX directory does not exist: {mtex_path_!r}.")

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
        if not Path(matlab_runtime_path).is_dir():
            raise ValueError(
                f"MATLAB runtime directory does not exist: {matlab_runtime_path!r}."
            )
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
