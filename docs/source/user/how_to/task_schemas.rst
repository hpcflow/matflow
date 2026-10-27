Task schemas
------------

Generating multiple load cases
==============================

The built-in ``generate_load_cases`` task generates a list of independent uniaxial
``LoadCase`` objects with identical loading parameters:

.. code-block:: yaml

    name: multiple_load_cases
    tasks:
      - schema: generate_load_cases_uniaxial
        inputs:
          num_load_cases: 3
          total_time: 100
          num_increments: 200
          direction: x
          target_def_grad_rate: 1.0e-3

``num_load_cases`` must be a positive integer. The ``load_case`` schema output has
``multiplicity: "<<input:num_load_cases>>"``, allowing downstream tasks to source
the individual load cases. With a multiplicity of one, the output remains a
single-member list, in accordance with the framework's multiplicity semantics.

Sampling EBSD textures with Python MTEX
======================================

The ``sample_texture_from_CTF_file_mtex_python`` and
``sample_texture_from_CRC_file_mtex_python`` schemas estimate an orientation density
from one EBSD phase and sample ``num_orientations`` orientations from it. They require
the Python edition of MTEX (``mtex>=1.0``) in ``python_env``; MATLAB is not needed.
The existing ``*_mtex`` schemas still use MATLAB.

.. code-block:: yaml

    tasks:
      - schema: sample_texture_from_CTF_file_mtex_python
        inputs:
          CTF_file_path: C:\data\texture.ctf
          specimen_symmetry: '1'
          EBSD_phase: Al
          num_orientations: 1000
          num_orientation_sets: 3
          kernel_halfwidth_deg: 10.0

For CRC data, use ``sample_texture_from_CRC_file_mtex_python`` and
``CRC_file_path`` instead. The matching ``.cpr`` file must be beside the ``.crc``
file, with the same stem.

``num_orientation_sets`` defaults to 1 and must be a positive integer. The density
is estimated once, then independently sampled for each set using the run's seeded
random generator. Each set contains ``num_orientations`` orientations.
The ``orientations`` output has multiplicity ``<<input:num_orientation_sets>>``:
its value is a list of orientation sets, including when the count is 1.
Downstream tasks sourcing ``orientations`` receive individual sets.

All inputs and the ``orientations`` output are passed directly to/from the script,
without JSON/HDF5 handoff files. There is no ``execution_mode`` input.
Sampling uses ``MATFLOW_RUN_RANDOM_SEED`` for reproducibility within Python MTEX;
samples are not expected to match MATLAB bit for bit. ``kernel_halfwidth_deg``
sets the density-estimation kernel halfwidth in degrees and defaults to ``10.0``,
preserving the previous smoothing choice. It must be finite, greater than zero,
and at most 180 degrees. The halfwidth is passed explicitly to MTEX, so it no
longer warns about selecting a default for correlated EBSD pixels.

``EBSD_reference_frame_transformation`` defaults to ``euler_to_spatial`` (also
accepted as ``convertEuler2SpatialReferenceFrame``), using the reader's Oxford
Euler correction. ``spatial_to_euler`` (or
``convertSpatial2EulerReferenceFrame``) leaves the Euler angles unchanged, as does
a null transformation: spatial coordinates are not part of this task's output.
The distinction matters because passing ``None`` as the reader's correction asks
MTEX to apply its default Oxford correction, while an explicit identity rotation
leaves the file's Euler angles unchanged.

``EBSD_rotation`` optionally applies a rigid map rotation specified by three
``euler_angles_deg``. By default, both map positions and orientations are rotated.
``keep_XY: true`` keeps map positions fixed and rotates orientations;
``keep_euler: true`` keeps orientations fixed and rotates map positions. The flags
cannot both be true. Since this task samples only orientations, ``keep_euler: true``
does not change the sampled texture.

The returned orientations use scalar-first inverse MTEX quaternions and the
crystal frame's unit-cell alignment. A frame whose Cartesian axes cannot all be
described by MatFlow lattice directions is rejected explicitly.

MATLAB MTEX compatibility
~~~~~~~~~~~~~~~~~~~~~~~~

The ``sample_texture_from_CTF_file_mtex`` and
``sample_texture_from_CRC_file_mtex`` schemas accept the same sampling inputs,
including ``kernel_halfwidth_deg`` with the same default and valid range,
reference-frame aliases, and rotation flags. ``spatial_to_euler`` (or
``convertSpatial2EulerReferenceFrame``) leaves Euler angles unchanged in both
implementations; ``euler_to_spatial`` applies the Oxford correction. They retain
JSON input/HDF5 output and the ``script``, ``compile``, and ``precompiled``
execution modes. Their output continues to use scalar-first inverse MTEX
quaternions and crystal alignment. Both implementations use the run's random
seed, but do not produce identical samples.

The MATLAB schemas sample one orientation set per task. ``num_orientation_sets``
is currently supported only by the Python MTEX schemas.

Both implementations read ``MATFLOW_RUN_NUM_THREADS`` from the run's
``num_threads`` resource (default 1). Python sets MTEX's ``threads`` preference;
MATLAB sets its computational thread limit using ``maxNumCompThreads``. MATLAB
MTEX's separate NFFT/MEX libraries may have their own threading limits.

Use ``execution_mode: script`` or recompile with ``execution_mode: compile`` to
use the updated MATLAB behavior. Existing precompiled executables must be rebuilt
from the updated scripts; changing the schema does not update those binaries.

Plotting orientations with Python MTEX
=====================================

The ``visualise_orientations_pole_figure_mtex_python`` and
``visualise_orientations_inverse_pole_figure_mtex_python`` schemas are Python
alternatives to the corresponding MATLAB ``*_mtex`` schemas. They require Python
MTEX (``mtex>=1.0``) in ``python_env`` and pass inputs directly to the script,
without JSON/HDF5 handoff files or an ``execution_mode`` input.

For example, append these tasks after an orientation-sampling task:

.. code-block:: yaml

    - schema: visualise_orientations_pole_figure_mtex_python
      inputs:
        crystal_symmetry: cubic
        pole_figure_directions: [[0, 0, 1], [1, 0, 1], [1, 1, 1]]
        use_contours: false
        IPF_reference_direction: z

    - schema: visualise_orientations_inverse_pole_figure_mtex_python
      inputs:
        crystal_symmetry: cubic
        IPF_reference_directions: [x, y, z]
        use_contours: true

Each task consumes a single ``orientations`` value. When a sampling task produces
multiple orientation sets, output multiplicity creates one plotting element per
set automatically.

Both quaternion component orders are supported. MatFlow's inverse quaternions
are converted back to MTEX's crystal-to-specimen convention, with the input
unit-cell alignment preserved. Euler-angle inputs are not supported and raise
an explicit error. As in the MATLAB tasks, the crystal frame is constructed from
``crystal_symmetry`` and the alignment, using MTEX's default lattice parameters.

``use_contours: false`` draws scatter plots; pole-figure markers use IPF colours
for ``IPF_reference_direction`` (x, y or z, default z). Inverse-pole-figure markers
are uncoloured, as in the MATLAB task, with one panel per
``IPF_reference_directions`` entry (default ``[z]``). Both scatter tasks also save
an IPF colour key. ``use_contours: true`` instead draws filled density contours
and colourbars, without a colour-key image. For pole figures,
``colourbar_limits`` optionally supplies two finite, increasing values, and
``use_one_colourbar: true`` uses a shared colour scale and a single bar. These
colourbar options apply only to contour plots.

The files are saved as ``pole_figure.png`` or ``inverse_pole_figure.png`` and,
for scatter plots, ``IPF_key.png``. The existing file labels
``mtex_pole_figures``, ``mtex_inverse_pole_figures`` and ``mtex_IPF_key`` are
retained, so the images are saved as workflow artifacts just as for MATLAB.
Rendering is headless, uses x pointing east, and closes its figures after saving.
``MATFLOW_RUN_NUM_THREADS`` controls MTEX's thread preference, as for Python
texture sampling. Figure styling and density contours may differ from MATLAB.

Action command strings
======================

An action command string, ``COMMAND_STRING``, determines what the action should actually run, and is specified within a task schema definition like this (where schema inputs/outputs have been omitted for brevity):

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs: ...
            outputs: ...
            actions:
              - environments:
                  any: python_env
                commands:
                  - command: COMMAND_STRING

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=...,
                outputs=...,
                actions=[
                    hf.Action(
                        environments=[hf.ActionEnvironment("python_env", scope="any")],
                        commands=[hf.Command("COMMAND_STRING")],
                    )
                ]
            )

Action command strings may contain the following variables:

- ``<<executable:EXE_NAME>>`` where ``EXE_NAME`` is the label of an environment executable that is defined within the action's environment.
- ``<<parameter:PARAM_NAME>>`` where ``PARAM_NAME`` is an input or output parameter type of the task schema that contains the action.
- ``<<args>>``, which corresponds to the list of items in the ``args`` attribute of the command, and will be formatted as a space-separated list.
- ``<<VAR_NAME:VAR_VALUE>>`` where ``VAR_NAME`` and ``VAR_VALUE`` correspond to items in the ``variables`` attribute of the command. This is used internally (when running scripts, for example, to pass information about the script name and path), but is typically not used when defining commands.

Parameter flow within task schemas
==================================

In addition to an actual implementation of the task, task schemas also define a mapping between input and output types. Within a task schema, multiple actions can use those inputs and outputs in different ways. For a simple example, a task schema with one input, ``p1``, and one output, ``p2``, might include a single action that consumes the schema input and produces the schema output:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml
        
            objective: t1
            inputs:
              - parameter: p1
            outputs:
              - parameter: p2
            actions:
             - commands:
                 - command: echo $((<<parameter:p1>> + 1))
                   stdout: <<parameter:p2>>

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p2")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p1>> + 1))",
                                stdout="<<parameter:p2>>"
                            )
                        ],
                    ),
                ],
            )

It is useful to understand the difference between task schema inputs and outputs, and action-level inputs and outputs. Task schema inputs and outputs are those parameters defined in the ``inputs`` and ``outputs`` attributes of the task schema. In particular, these are represented by the ``SchemaInput`` and ``SchemaOutput`` objects. ``SchemaInput`` objects, in their most basic form, simply point to a parameter type, e.g. ``p1``. However, they may also include other information, such as a default value, and whether the parameter can be used in multiple labelled forms, which is a useful facility when inputs of the same type that originate from different tasks (or element sets) should be distinguished.

As checked during task schema validation, it's a requirement that the schema-level inputs and outputs are compatible with the actions of the that task schema. This means that the constituent actions of the task schema consume and produce parameters in a way that is commensurate with their parent task schema. For example, in the simple case of a task schema that has a single action with a command string ``echo <<parameter:p1>>``, the task schema must include an schema input of the ``p1`` parameter type. Conversely, if the task schema includes an input ``p1``, then it must be consumed by one of the task schema's actions.

But what constitutes action-level inputs (or consumers) and outputs (or producers)? The simplest examples to demonstrate this are those seen above, where we define a command string that includes references to an input parameter (e.g. ``command="echo $((<<parameter:p1>> + 1))"``), and we use the ``stdout`` command attribute to map the shell standard output from the command string back to an output parameter (e.g. ``stdout="<<parameter:p2>>"``). So in this case the action level inputs and outputs are ``p1`` and ``p2`` respectively. However, action level inputs and outputs can also be defined from scripts. Currently, the action-level inputs and outputs for script actions are simply set to those from the task schema, but this will be refined in future to improve validation (since a script may not require all inputs of a task schema, and/or it might not generate all task schema outputs).

.. note::

   Don't worry about getting this wrong! |app_name| will tell you if you are trying to define a task schema whose actions are not compatible with the schema's inputs and outputs.

It's important to note that in the examples above, we use the substitution syntax ``<<parameter:INPUT_OR_OUTPUT_TYPE>>`` within the command string and the standard output string (``stdout``). We use the term ``parameter`` because we can reference both inputs and outputs within actions. We do this in the following example, where the task schema input ``p1`` is used in the first action to generate the task schema output ``p2``, but we additionally include a second action which uses (as an action-level input) the task schema output ``p2``:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs:
            - parameter: p1
            outputs:
            - parameter: p2
            actions:
            - commands:
                - command: echo $((<<parameter:p1>> + 1))
                  stdout: <<parameter:p2>>
            - commands:
                - command: echo <<parameter:p2>> # note: schema output `p2` used as an action input

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p2")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo <<parameter:p1>>",
                                stdout="<<parameter:p2>>",
                            )
                        ]
                    ),
                    hf.Action(  # note: schema output `p2` used as an action input
                        commands=[
                            hf.Command(command="echo <<parameter:p2>>")
                        ]
                    ),
                ],
            )

Additionally, an action may output a parameter that is *not* a task schema output, as long as it is used as an input in a downstream action within the same task schema, as in this example, where the task schema converts its input ``p1`` to its output ``p3`` via an intermediate parameter ``p2``, which is an *output* of the first action, and an *input* of the second action:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs:
            - parameter: p1
            outputs:
            - parameter: p3
            actions:
            - commands:
                - command: echo $((<<parameter:p1>> + 1))
                  stdout: <<parameter:p2>> # note: action output `p2` is not a schema-level output
            - commands:
                - command: echo $((<<parameter:p2>> + 1))
                  stdout: <<parameter:p3>>

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p3")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p1>> + 1))",
                                stdout="<<parameter:p2>>",  # note: action output `p2` is not a schema-level output
                            )
                        ]
                    ),
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p2>> + 1))",
                                stdout="<<parameter:p3>>",
                            )
                        ]
                    ),
                ],
            )

Show information about a task schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Python API, use the `info` property of a task schema object to print information such as the input and output parameters of the schema: :code:`TaskSchema.info`.
