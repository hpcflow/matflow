MatFlow and DAMASK in one container
==================================

``Dockerfile.damask_grid`` layers MatFlow, hpcflow and JupyterLab onto a DAMASK
runtime with system Python 3.13. Build and runtime use the same base, so the
virtual environment reuses its Python installation and shared libraries instead
of copying a second Python runtime from a Debian image. MPI and UCX are retained.

.. warning::

   The Python 3.13 base below uses Ubuntu 25.10, which is end-of-life. This is a
   size-reduction experiment, not a supported production deployment. The previous
   ``matflow:damask`` image is retained; experimental builds use a separate tag.

The measured Docker image sizes were 1.81 GB for ``matflow:damask`` and 1.68 GB
for ``matflow:damask-py313`` (approximately 7% smaller). The DAMASK base decreased
from 932 MB to 857 MB. These are Docker's displayed image sizes, not archive
download sizes. The environment still contains the scientific Python dependencies;
the saving comes from the changed base and removal of the duplicate interpreter,
not sharing NumPy or SciPy with DAMASK (the solver package does not require them).

DAMASK remains version 3.1.0, but Ubuntu 25.10 supplies Open MPI 5.0.8 and PETSc
3.22.5 instead of Open MPI 5.0.10 and PETSc 3.24.4 in the previous base.
The smoke tests validate solver startup and workflow persistence, not numerical
equivalence of simulation results between these library versions.

First rebuild the DAMASK runtime with system Python and venv support:

.. code-block:: powershell

    docker build -f D:\projects\damask-docker\Dockerfile.damask-grid `
        --build-arg UBUNTU_VERSION=25.10 `
        -t mydamask:py313 D:\projects\damask-docker

Build from the MatFlow repository, supplying the current hpcflow checkout as a
named Docker BuildKit context:

.. code-block:: powershell

    docker build -f Dockerfile.damask_grid `
        --build-context hpcflow=D:\projects\hpcflow `
        --build-arg DAMASK_IMAGE=mydamask:py313 `
        --build-arg MATFLOW_IMAGE=matflow:damask-py313 `
        -t matflow:damask-py313 .

The DAMASK base must already exist locally or be available from a registry.
The default is ``mydamask:py313``. The build validates Python 3.13 before
installing application dependencies. The DAMASK Dockerfile still defaults to
``UBUNTU_VERSION=rolling`` when no override is supplied, but that rolling image's
Python may be too new for this combined-image build.

Additional Python packages for this image are listed in
``requirements.damask_grid.txt``, currently ``damask`` and ``damask-parse``.
They are installed into the same virtual environment as MatFlow and JupyterLab.
Edit this file and rebuild the image to add further packages. These requirements
are unpinned, so a fresh dependency installation resolves the available compatible
versions; they do not change MatFlow's ordinary installation dependencies.

The final image does not run another container internally. Both applications
are installed in the same image; the default entrypoint is MatFlow. The
``MATFLOW_IMAGE`` build argument must match the final tag so exported wrappers
select the correct image. The supplied hpcflow checkout must include container
and notebook support (currently version 0.3.0a9).

Host wrapper and notebooks
-------------------------

Export the standalone host wrapper without installing Python on the host:

.. code-block:: powershell

    docker run --rm matflow:damask-py313 install > matflow.ps1
    .\matflow.ps1 --help
    .\matflow.ps1 notebook

Run from the directory containing your notebooks and workflows. JupyterLab
prints a token-authenticated localhost URL; open it in a browser or connect
VS Code using its existing Jupyter server kernel selector. Use
``-NotebookPort 8889`` to change the host port. Files under ``/work`` are saved
in the host working directory. MatFlow's configuration, cache and data use
the persistent ``.matflow-container`` directory, separate from native MatFlow.

For notebook access to a workflow:

.. code-block:: python

    import matflow as mf

    workflow = mf.Workflow("/work/my_workflow")

Invoking DAMASK
---------------

Override the entrypoint to run the simulation executable from the same image:

.. code-block:: powershell

    docker run --rm --entrypoint DAMASK_grid matflow:damask-py313 --help
    docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/work" `
        --workdir /work --entrypoint DAMASK_grid matflow:damask-py313 `
        --geom geom.vti --load load.yaml --material material.yaml

Inputs and results stay in the host working directory. To invoke an MPI
launcher instead, use ``--entrypoint mpirun`` with the appropriate launcher
arguments and ``DAMASK_grid`` as the executable. The base image's
``OMP_NUM_THREADS=1`` default is preserved; override it explicitly if needed.
Host MPI/scheduler integration and RDMA device access still require
site-specific configuration; this image does not automatically expose devices
or provide compatibility with a host MPI installation.

DAMASK can also be invoked with ``subprocess.run`` in a notebook kernel,
because its executable is on the container's ``PATH``. Host-only commands
such as ``srun`` must still be launched by the host wrapper or scheduler.

Putting the executable in the image does not automatically configure a
MatFlow workflow's DAMASK environment. The existing DAMASK environment setup
supports a host-side Docker command; use its additional options to override
this image's MatFlow entrypoint and ``/work`` default directory:

.. code-block:: powershell

    matflow --config-dir "$HOME\.matflow-container" env setup damask `
        --docker-image matflow:damask-py313 `
        --option entrypoint DAMASK_grid --option workdir /wd

The environment setup mounts the host task directory at ``/wd``. Use these
options whenever selecting the combined image instead of a DAMASK-only image.
Run setup on the host (or supply equivalent executable configuration); do not
attempt to run Docker inside the simulation container.
This example requires a native MatFlow installation on the host and uses the
wrapper's default shared configuration directory. If ``MATFLOW_CONFIG_DIR`` is
set, pass its corresponding ``-container`` directory instead. Native MatFlow's
ordinary configuration directory is not shared with the wrapper by default.

Validation
----------

The image smoke tests check both entrypoints, exported wrapper namespacing,
the Python runtime, and workflow creation/reloading through a persistent mount.
Using a configured MatFlow Python environment, select the image and run:

.. code-block:: powershell

    $env:MATFLOW_TEST_CONTAINER_IMAGE = "matflow:damask-py313"
    matflow test --integration --configure-python-env -k test_combined_container
