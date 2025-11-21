"""
Runs the command line interface.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
from hpcflow.sdk.submission.shells import DEFAULT_SHELL_NAMES


import matflow as mf
from matflow import cli
from matflow.environments import (
    env_configure_python,
    env_configure_python_all,
    env_configure_dream3d,
    env_configure_matlab,
)


if TYPE_CHECKING:
    from hpcflow.sdk.app import BaseApp


def add_to_env_setup_CLI(app: BaseApp) -> click.Group:
    """Generate the CLI for configuring MatFlow environments."""

    shell = DEFAULT_SHELL_NAMES[os.name]

    @click.command()
    @click.option(
        "-p",
        "--pipeline-runner-path",
        required=True,
        type=click.Path(exists=True, file_okay=True),
        help="Absolute path to the pipeline runner executable.",
    )
    @click.option(
        "--use-current/--no-use-current",
        is_flag=True,
        default=True,
        help=(
            "Use the currently active conda-like or Python virtual environment to add a "
            "`python_script` executable to the environment."
        ),
    )
    def dream3d(pipeline_runner_path: Path, use_current: bool):
        """Configure the Dream3D environment.

        The path to the PipelineRunner executable must be provided.

        """
        env = env_configure_dream3d(
            shell,
            pipeline_runner_path=pipeline_runner_path,
            use_current=use_current,
        )
        app.save_env(env)

    @click.command()
    @click.option(
        "-n",
        "--name",
        multiple=True,
        help=(
            "In addition to the `python_env` set up these other named environments "
            '(suffixed by "_env"), also with a `python_script` executable.'
        ),
    )
    @click.option(
        "--use-current/--no-use-current",
        is_flag=True,
        default=True,
        help=(
            "Use the currently active conda-like or Python virtual environment to add a "
            "`python_script` executable to the environment."
        ),
    )
    def python(name: list[str], use_current: bool):
        """Configure environments with `python_script` executables."""
        envs = env_configure_python(
            shell,
            names=name,
            use_current=use_current,
        )
        for env in envs:
            app.logger.debug(f"Saving 'python' environment: {env.name!r}.")
            app.save_env(env)

    @click.command()
    @click.option(
        "--use-current/--no-use-current",
        is_flag=True,
        default=True,
        help=(
            "Use the currently active conda-like or Python virtual environment to add a "
            "`python_script` executable to the environment."
        ),
    )
    def python_all(use_current: bool):
        """Configure all Python environments with the same setup."""
        envs = env_configure_python_all(shell, use_current=use_current)
        for env in envs:
            app.logger.debug(f"Saving 'python' environment: {env.name!r}.")
            app.save_env(env)

    @click.command()
    @click.option(
        "--path",
        type=click.Path(exists=True, dir_okay=True),
        help="Absolute path to the MATLAB installation directory.",
    )
    @click.option(
        "--runtime-path",
        type=click.Path(exists=True, dir_okay=True),
        help="Absolute path to the MATLAB runtime directory.",
    )
    @click.option(
        "--mtex-path",
        type=click.Path(exists=True, dir_okay=True),
        help="Absolute path to the MTEX installation directory.",
    )
    def matlab(path: Path, runtime_path: Path, mtex_path: Path):
        """Configure the MATLAB environment for running/compiling MTEX scripts."""
        env = env_configure_matlab(
            shell,
            matlab_path=path,
            matlab_runtime_path=runtime_path,
            mtex_path=mtex_path,
        )
        app.save_env(env)

    app.env_setup_CLI.add_command(dream3d)
    app.env_setup_CLI.add_command(python)
    app.env_setup_CLI.add_command(python_all)
    app.env_setup_CLI.add_command(matlab)


add_to_env_setup_CLI(mf)

if __name__ == "__main__":
    cli()
