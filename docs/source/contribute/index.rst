.. _contribute:

Contribute
##########



Recommended reads
=================
- `Conventional commits <https://www.conventionalcommits.org/en/v1.0.0/>`_
- `poetry <https://python-poetry.org/docs/>`_
- `click <https://click.palletsprojects.com/en/8.1.x/>`_


Installation for development
============================

`Install poetry <https://python-poetry.org/docs/#installation>`_ first.


Clone repo
-----------
Clone the git repo (see ssh links below), and then make sure that you switch to the development branch::

   git switch develop

This branch is protected, so create a feature branch before pushing to the repo.

Checking out hpcflow
....................
::

   git clone git@github.com:hpcflow/hpcflow-new.git

Checking out matflow
....................
::

   git clone git@github.com:hpcflow/matflow-new.git

Install python dependencies with poetry
---------------------------------------
You should be able to simply run::

   poetry install

from the hpc-flow folder and poetry will take care of everything for you.

Troubleshooting
................
If for some reason the install failed, try the following:

Delete the virtualenv. You first need to find the version you are using with::

   poetry env info

then use it to remove the virtual environment with::

   poetry env remove 3.10.6

Clear all cache in list with::

   poetry cache clear --all PyPI

Check if there is no cache with::

   poetry cache list

Reinstall dependencies::

   poetry install


Working from the source
=======================
Open the virtual enviroment with::

   poetry shell

Working with hpcflow
--------------------

You can interact with the CLI by calling::

   python3 hpcflow/cli/cli.py --help


Working with matflow
--------------------

link to local hpcflow
......................
To be able to work with hpcflow and immediately see the changes reflected in matflow you need to reconfigure the hpcflow dependency to point to your local copy of hpcflow.
To do this, run::

   poetry add --editable ${HOME}/hpcflow-new/

This will update the hpcflow-new dependency to point to your local copy.

If this does not work, try doing it manually:
First modify the ``matflow-new/pyproject.toml`` file replacing::

   hpcflow-new2 = "^0.2.0a14"

with::

   hpcflow-new2 = {path = "${HOME}/hpcflow-new", develop = true}

Then, you need to update your poetry environment accordingly, by first removing the lock file::

   rm poetry.lock

and then re-running the dependency installation::

   poetry install

CLI
...
You can interact with the CLI by calling::

   python3 matflow/cli.py --help
