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
    env_configure_moose,
    env_configure_python_all,
    env_configure_dream3d,
    env_configure_matlab,
    env_configure_damask,
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
        "--use-current/--no-use-current",
        is_flag=True,
        default=True,
        help=(
            "Use the currently active conda-like or Python virtual environment to add a "
            "`python_script` executable to the environment."
        ),
    )
    @click.option(
        "--replace/--no-replace",
        is_flag=True,
        default=False,
        help="If True, replace existing environments.",
    )
    def python_all(use_current: bool, replace: bool):
        """Configure all Python environments with the same setup."""
        envs = env_configure_python_all(shell, use_current=use_current)
        for env in envs:
            app.logger.debug(f"Saving 'python' environment: {env.name!r}.")
            app.save_env(env, replace=replace)

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

    @click.command()
    @click.option(
        "--docker-image",
        help=(
            "Name of the docker image to use to run DAMASK_grid; or the name of the "
            "image expected within the archive."
        ),
    )
    @click.option(
        "--docker-archive",
        help="Name of the docker archive to load the image from.",
    )
    @click.option(
        "--singularity-archive",
        help="Name of the docker archive to build a sif file from.",
    )
    @click.option(
        "--singularity-sif",
        help="Name of the singularity sif file to use.",
    )
    @click.option(
        "--docker-exe",
        default="docker",
        help="Docker executable file.",
    )
    @click.option(
        "--singularity-exe",
        default="singularity",
        help="Singularity executable file.",
    )
    def damask(
        docker_image: str | None,
        docker_archive: str | Path | None,
        singularity_archive: str | Path | None,
        singularity_sif: str | Path | None,
        docker_exe: str | Path,
        singularity_exe: str | Path,
    ):
        """Configure the DAMASK environment.

        In particular the `damask_grid` executable.

        """
        env = env_configure_damask(
            shell,
            docker_image=docker_image,
            docker_archive=docker_archive,
            docker_exe=docker_exe,
            singularity_archive=singularity_archive,
            singularity_sif=singularity_sif,
            singularity_exe=singularity_exe,
        )
        app.save_env(env)

    @click.command()
    @click.option(
        "--docker-image",
        help=(
            "Name of the docker image to use to run DAMASK_grid; or the name of the "
            "image expected within the archive."
        ),
    )
    @click.option(
        "--docker-archive",
        help="Name of the docker archive to load the image from.",
    )
    @click.option(
        "--singularity-archive",
        help="Name of the docker archive to build a sif file from.",
    )
    @click.option(
        "--singularity-sif",
        help="Name of the singularity sif file to use.",
    )
    @click.option(
        "--docker-exe",
        default="docker",
        help="Docker executable file.",
    )
    @click.option(
        "--singularity-exe",
        default="singularity",
        help="Singularity executable file.",
    )
    def moose(
        docker_image: str | None,
        docker_archive: str | Path | None,
        singularity_archive: str | Path | None,
        singularity_sif: str | Path | None,
        docker_exe: str | Path,
        singularity_exe: str | Path,
    ):
        """Configure the MOOSE (proteus) environment."""
        env = env_configure_moose(
            shell,
            docker_image=docker_image,
            docker_archive=docker_archive,
            docker_exe=docker_exe,
            singularity_archive=singularity_archive,
            singularity_sif=singularity_sif,
            singularity_exe=singularity_exe,
        )
        app.save_env(env)

    app.env_setup_CLI.add_command(dream3d)
    app.env_setup_CLI.add_command(python_all)
    app.env_setup_CLI.add_command(matlab)
    app.env_setup_CLI.add_command(damask)
    app.env_setup_CLI.add_command(moose)


add_to_env_setup_CLI(mf)

if __name__ == "__main__":
    cli()
