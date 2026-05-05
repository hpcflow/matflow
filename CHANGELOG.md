
<a name="v0.3.0"></a>
## [v0.3.0](https://github.com/hpcflow/matflow/compare/v0.2.26...v0.3.0) - 2026.05.05

### ♻ Code Refactoring

* toy model sus
* move `env_configure_python` to hpcflow
* remove unused imports
* rename matflow-new to matflow
* move build_surrogate task schemas
* defer imports
* ensure both `target_def_grad_(rate)` and `strain_(rate)` are populated in `LoadStep.uniaxial`
* reuse util function from hpcflow
* remove unused sentry dep
* move example data files
* Sync workflows and docs with remotes.
* conf.py include only app specific, and imports config_common
* allow access to app log in ParameterValue classes
* rename generate_volume_element from_random_voronoi method to from_voronoi
* reflect upstream hpcflow SDK restructure
* add api imports
* store RunTimeInfo in MatFlow obj

### ✨ Features

* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* record SuS acceptance rate for each level
* support arbitrary proposal distributions in `generate_next_state`
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* support random seed in `seeds_from_random`
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* set matlab RNG in MTEX scripts
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* updates to moose schemas
* add `MooseInputDeck` parameter value class
* add damask_from_input_files demo to compare with moose_from_files
* add moose input file demo
* bump hpcflow version
* add env setup damask
* bump hpcflow version
* add macos MTEX programs
* update data manifest for linux mtex programs
* bump hpcflow version
* add `matflow env setup` for various envs
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add first linux MTEX program
* update sample_texture_model_ODF
* update MTEX tasks to include precompiled execution mode
* bump hpcflow version
* move data/programs to a separate repo
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* use surrogat demo data
* bump hpcflow version
* add `perform_inference` task
* add fit_surrogate task
* implement mesh refinement and inverse optimisation MOOSE workflows
* bump hpcflow version
* initial surrogate model support
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* continue supporting DAMASK v3.0.0-alpha7 (requires https://github.com/hpcflow/hpcflow-new/pull/892)
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add support for specifying DAMASK `initial_conditions`
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* initial support for CIPHER simulations
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add a demo workflow for demostrating different MTEX script exec modes
* add plate geometry moose workflow
* bump hpcflow version
* bump hpcflow version
* use template in gmsh mesh generation workflow
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* option to run `sample_texture_CTF` from a precompiled program
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* initial support for CIPHER simulations
* add some parametrisation to plate-with-hole
* some initial basic gmsh integration
* bump hpcflow version
* add `target_strain` and `target_strain_rate` args to `LoadStep.unaxial` for convenience
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* added optional columns parameter to the from_file methods in microstructure seeds
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add non-periodic option to generate volume element by voronoi
* bump hpcflow version
* bump hpcflow version
* support python 3.13, and use it github actions workflows
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* support failure handling in subset sim workflows
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add initial multi-level (two-level) MCMC subset-sim workflow
* bump hpcflow version
* add subset-sim DAMASK-Mg adaptive proposal workflow
* add toy model adaptive subset-sim workflow that uses a non-Python performance func
* split subset-sim workflows into Al and Mg
* add bool parameter to remove DAMASK hdf5 file in get_yield_stress OFP
* add task generate_next_state_CS for subset-infinity/conditional sampling
* add task to plot IPF with MTEX
* bump hpcflow version
* bump hpcflow version
* Add MOOSE simualtions
* add acceptance rate and propoal stddev parameter to subset workflows
* add variations of subset simulation workflow
* use `combine_scripts` and loop termination condition in subset sim workflow
* bump hpcflow version
* add a task schema for damask simulation that uses fewer parameters (and so files)
* bump hpcflow version
* update subset simulation demo workflow, simplify parameters
* initial implementation of subset simulation
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add multistep random loadcase with interpolation
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow
* bump hpcflow version
* bump hpcflow version
* implement sample_texture_random using mtex
* implement sample_orientation_from_CRC workflow
* implement sample_orientations_from_CTF workflow
* modify VE grid size using damask
* bump hpcflow version
* add scale_morphology parameter to generate VE voronoi
* bump hpcflow version
* bump hpcflow version
* update RVE_extrusion demos to include DAMASK sim
* bump hpcflow version
* add damask numerics file and example
* implement 'sample texture from crc file' using mtex
* add `modify_VE_add_buffer_zones` task schema
* add `generate_volume_element_extrusion` task schema
* bump hpcflow version
* add `load_microstructure` task schema using DefDAP
* parse dream_3D volume element
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* improve task schema Sphinx docs
* bump hpcflow version
* bump hpcflow version
* add demo workflow to show passing damask input files directly
* add task schema generate_volume_element_from_statistics
* bump hpcflow version
* add WIP demo workflow for simulating a known-texture yield surface
* add schema visualise_volume_element
* add schema sample_texture_from_model_ODF
* support specifying damask solver
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add demo fitting workflow
* bump hpcflow version
* add `SingleCrystalParameters` class
* add read_tensile_test
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add demo-data
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add plot_pole_figures
* bump hpcflow version
* bump hpcflow version
* add task method sample_texture from_ODF_mat_file with MTEX
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add fit yield func demo workflow
* bump hpcflow version
* update schemas
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add MicrostructureSeeds.show`
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* Adds script to configure and sync remotes
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* add stub environments
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* bump hpcflow version
* initial support of fit yield function workflow
* bump hpcflow for groups
* add task dump_all_yield_stresses
* add MicrostructureSeeds parameter class
* refine Orientations
* bump hpcflow
* add orientations parameter to generate_volume_element_random_voronoi
* support non-compiled MTEX scripts as well as compiled scripts
* update task schemas to reflect upstream changes
* add sample_texture task
* bump deps
* bump hpcflow
* add viz to damask task
* test-pre-python workflow to allow dispatch from dev branch
* flesh out simple damask workflow
* dummy commit
* start damask support
* capitalise app name
* Update ubuntu runner for build documentation
* Add compress scripts for onefile builds
* add logging
* update deps
* test dev build

### 🐛 Bug Fixes

* import error
* variables in test-demos for PR-triggered run
* docker run command in damask env setup
* pass permissions to damask docker image command in test-demos
* missing pip dep
* test-demos
* test-demos
* add random seed to toy model subset simulation demo
* tweaks to subset simulation to make reproducible via random seed
* script `modify_VE_spread_orientations` so Zarr arrays are cast to numpy
* random
* fix typo in Configure Poetry in Release WF
* Try specific code-block commands
* estimation of CoV in subset sim collate_results
* disable DAMASKs parallel VTK writing on Windows
* respect config overrides in `isolated_app_config` fixture
* add missing groups in subset sim workflows
* add missing hidden import
* cli tests
* tests
* remove deprecated py3.9 support
* remove duplicate method `LoadStep.random_inc` (my fault!)
* some env fix
* some env fix
* updates to env setup
* various updates
* small changes to moose stuff
* assume scalar data in `parse_exodus` if shape not in lookup
* rename basic moose workflow
* basic moose workflow
* set executable bit on additional files for mtex programs
* set both the shell script and the binary to executable for linux MTEX program
* manifest for sample_texture_CTF linux program
* pyinstaller hook
* remove outstanding `compile:` keys for MTEX task demo workflows
* update MTEX demo workflows
* update default config dir to `~/.matflow`
* visualise_VE
* typing in py3.9
* tidying up the `Surrogate` class
* missing lock
* indent!
* remove commented-out
* tidy up lm_fit_moose
* moose mesh refine workflow
* schemas
* combining support for old and new DAMASK
* update damask high-concurrency schema
* DAMASK command line for v3.0.2
* to reflect changes in default input sources behaviour in hpcflow
* demo of how to implement `from_statistics_dual_phase_orientations`
* add builtin jinja templates to pyinstaller hook
* add missing __init__.py
* update gmsh workflow
* task parametrisation
* IFG inputs and format escpaing
* missing import!
* allow failure on macos for a test that gets rate-limited by github
* perturbations is a list in `SingleCrystalParameters`
* missing import
* failing macos (built executable) test due to rate limit
* run poetry lock
* do not trigger testing on PR edit event
* some updates to SuS workflows
* fix scipy pyinstaller issue
* update envs examples
* sync upstream shared docs and GHAs workflows
* sync upstream shared docs and GHAs workflows
* subset_simulation parameter flow tests
* better support 1D subset-simulation problems
* test test_subset_sim_DAMASK_Mg_two_level_parameter_flow
* add missing import
* add tests for YAML-initialising load case, seeds, orientations
* centOS GHAs
* reuse env to reduce number of jobscripts in subset-sim two-level DAMASK
* enable compatibility with new DAMASK Grid variable
* allow using pre-defined orientations in Dream 3D stats generator
* allow using pre-defined orientations in Dream 3D stats generator
* delete damask HDF5 files in subset-sim workflows
* quaternion vector sign in MTEX plot-IPF script
* add missing scripts for adaptive subset-infinity
* retrieval of loop iteration index in `collate_results`
* improvments to DAMASK subset workflow
* prevent `geom_load.hdf5` saving as artifact in `yield_stress` output file parser
* update subset workflow to speed up MMA
* update GHA workflows
* update GHA workflows
* bump pyinstaller, try to fix build error
* hpcflow api use
* quaternion vector sign in MTEX scripts
* logging in subset sim workflow script
* add a download-artifact[@v3](https://github.com/v3) step in release-github-PyPI to grab CentOS (docker) built executable which cannot use upload-artifact[@v4](https://github.com/v4)
* bump deps
* typos in `LoadStep`
* remove unused imports
* defer matplotlib import to speed up import time
* add default repeats value to string variable substitution workflow
* add link to schema documentation
* add link to schema documentation
* add link to documentation
* add README tick to show workflow implemented
* update README to show workflow is implemented
* update README to indicate implemented workflow
* remove unused function
* make function match file name
* use demo-data in `sample_texture_CRC_file`
* demo workflow texture symmetry in simulate_yield_surface_2D_brass
* material parameters in RVE_extrusion demo workflows
* whitespace
* whitespace
* whitespace and readme table links
* add missing env stub
* remove non-breaking spaces from new demo workflows
* numerics parameter name in new demo workflows
* add validation of new VE
* remove unused import
* save dream3d files in workflow directory
* bug in `LoadStep.plane_strain` class method; fix [#194](https://github.com/hpcflow/matflow/issues/194)
* remove extraneous template components
* add rule to damask_viz_result output file parser
* use random orientations if none passed to `MicrostructureSeeds`
* build-exes when only build dirs
* remove unused import
* parse masked arrays from lists in `LoadStep`
* make_vers_switcher invocation
* merge from upstream
* demo_data_dir
* update conftest.py
* missing `BaseApp` attributes
* replaced head_ref with ref_name to prevent fail if branch is deleted
* test_direct_sub schemas to schema
* sample_texture task schema rules
* missing jinja raw
* demo_sleep remove abortable for now; fails on some powershell
* schemas ref again
* schemas ref
* demo workflow upstream change
* "path: resources.os_name"
* action rule path
* try demo workflow file output in docs
* docs and add default_known_configs_dir
* docs link in README
* docs link in README
* deps
* add test deps
* change default config dir so it does not conflict with old install
* Use standard sphinx code-block commands
* scripts dir
* bump hpcflow
* docs build
* bump hpcflow
* fit_yield_function script, cast zarr arrays to numpy
* update gitignore
* make OrientationRepresentation store-encodable and fix matlab hdf5 orientation export
* flesh out LoadCase and add LoadStep class
* use Orientations-compatible dict in MicrostructureSeeds object
* bump hpcflow
* no need to return ori_data in sample_texture_CTF.m
* bump hpcflow for bug fix
* bump hpcflow
* bump deps
* bump hpcflow
* bump deps
* bump hpcflow
* version bump for hpcflow
* loading task schemas without defined envs
* write load case bug
* pip install dist name
* writing empty damask numerics file
* hard code damask env for now
* hpcflow version test
* **GHA:** add app_name variable
* **GHA:** testing
* **GHA:** testing
* **GHA:** testing
* **gha:** update poetry check pre-commit rev
* **gha:** version check
* **pyi:** hook datas typo
* **pyi:** hidden import
* **pyi:** data package
* **subset:** temp comment out logs and prints for now
* **subset-sim:** maintain structure of g for indicator functon
* **subset-sim:** missing modifications to `collate_results` task schema
* **subset-sim:** update toy model prop std to 1.0; works much better

### 👷 Build changes

* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* sync updates from docs repo
* sync updates from CI and docs repos
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update GH action workflows to reflect recent upstream changes
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into workshop-prep
* update binary download links file [skip ci]
* merge branch 'develop' into fix/macos-mtex
* update binary download links file [skip ci]
* merge branch 'env/docker' into bump/hpcflow
* update binary download links file [skip ci]
* merge in develop
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into feat/configure-env
* merge branch 'bump/hpcflow' into feat/set-executable
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into feat/program-extra-files
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into feat/programs
* merge branch 'develop' into feat/programs
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge in develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into fix/visualise_VE
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into fix/surrogate-tidy
* update binary download links file [skip ci]
* merge in develop
* merge in develop
* update binary download links file [skip ci]
* merge branch 'develop' into software/moose
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into software/damask_beta0
* merge branch 'develop' into software/damask_beta0
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge in develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'bump/hpcflow' into fix/default-inp-sources
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge
* merge branch 'develop' into software/moose
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into feat/programs
* update binary download links file [skip ci]
* merge
* merge branch 'software/gmsh' into software/moose
* merge in develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into feat/microstructure_generation
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* merge branch 'develop' into test/params
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge branch 'fix/mtex-oris' of https://github.com/hpcflow/matflow-new into fix/mtex-oris
* change back to LF endings
* merge develop
* bump deps
* update binary download links file [skip ci]
* merge branch 'develop' into uq/subset-simulation
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* sync GHA updates
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* sync GHA updates
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* sync upstream GHA templates
* update binary download links file [skip ci]
* sync upstream GHA templates
* update binary download links file [skip ci]
* sync upstream GHA templates
* update binary download links file [skip ci]
* fix poetry lock
* sync upstream GHA templates
* bump highest supported python to 3.12
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge upstream
* update binary download links file [skip ci]
* update gitignore
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge upstream python-release-workflow
* update binary download links file [skip ci]
* merge upstream python-release-workflow
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update lock
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update poetry lock
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge from develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* sync-updates GH Actions workflow templates
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* merge from develop
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update GH Actions workflows
* sync-updates GH Actions workflow templates
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* bump lock
* update binary download links file [skip ci]
* bump deps
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* update pyproject.toml, poetry.lock
* update deps
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* Updated gha workflows
* update binary download links file [skip ci]
* reset versions
* update binary download links file [skip ci]
* update binary download links file [skip ci]
* bump deps
* upstream various
* update binary download links file [skip ci]
* fix release to non-test pypi
* update binary download links file [skip ci]
* merge in develop
* release to non-test PyPI as matflow-new
* fix GHA git perms
* update deps
* update poetry
* deps
* update deps
* update GH actions template
* update GH actions template data
* update git perms
* update pyi scripts
* update deps
* update pre-commit
* update pre-commit
* update GH actions workflows
* update deps
* update gitignore
* update binary download links file [skip ci]
* revert "bump: 0.3.0a1 → 0.3.0a2 [skip ci]"
* poetry update
* add poetry pre-commit
* delete pyinstaller build dirs
* change commitizen bump message to skip ci
* update binary download links file [skip ci]
* initial setup
* **GHA:** Update workflow template files.
* **GHA:** Update workflow files

### 🔄 Updates

* support damask v3 beta0
* deps


<a name="v0.2.26"></a>
## [v0.2.26](https://github.com/hpcflow/matflow/compare/v0.2.25...v0.2.26) - 2022.03.18

### 🐛 Bug Fixes

* bug in scripting module
* print full exception from bad output map


<a name="v0.2.25"></a>
## [v0.2.25](https://github.com/hpcflow/matflow/compare/v0.2.24...v0.2.25) - 2021.12.20

### 🐛 Bug Fixes

* prep/proc run options ignored on load


<a name="v0.2.24"></a>
## [v0.2.24](https://github.com/hpcflow/matflow/compare/v0.2.23...v0.2.24) - 2021.10.06


<a name="v0.2.23"></a>
## [v0.2.23](https://github.com/hpcflow/matflow/compare/v0.2.22...v0.2.23) - 2021.10.06


<a name="v0.2.22"></a>
## [v0.2.22](https://github.com/hpcflow/matflow/compare/v0.2.21...v0.2.22) - 2021.08.14


<a name="v0.2.21"></a>
## [v0.2.21](https://github.com/hpcflow/matflow/compare/v0.2.20...v0.2.21) - 2021.06.06


<a name="v0.2.20"></a>
## [v0.2.20](https://github.com/hpcflow/matflow/compare/v0.2.19...v0.2.20) - 2021.05.12


<a name="v0.2.19"></a>
## [v0.2.19](https://github.com/hpcflow/matflow/compare/v0.2.18...v0.2.19) - 2021.04.12


<a name="v0.2.18"></a>
## [v0.2.18](https://github.com/hpcflow/matflow/compare/v0.2.17...v0.2.18) - 2021.04.10


<a name="v0.2.17"></a>
## [v0.2.17](https://github.com/hpcflow/matflow/compare/v0.2.16...v0.2.17) - 2021.02.15


<a name="v0.2.16"></a>
## [v0.2.16](https://github.com/hpcflow/matflow/compare/v0.2.15...v0.2.16) - 2021.02.05


<a name="v0.2.15"></a>
## [v0.2.15](https://github.com/hpcflow/matflow/compare/v0.2.14...v0.2.15) - 2021.01.18


<a name="v0.2.14"></a>
## [v0.2.14](https://github.com/hpcflow/matflow/compare/v0.2.13...v0.2.14) - 2021.01.17


<a name="v0.2.13"></a>
## [v0.2.13](https://github.com/hpcflow/matflow/compare/v0.2.12...v0.2.13) - 2020.12.17


<a name="v0.2.12"></a>
## [v0.2.12](https://github.com/hpcflow/matflow/compare/v0.2.11...v0.2.12) - 2020.12.16


<a name="v0.2.11"></a>
## [v0.2.11](https://github.com/hpcflow/matflow/compare/v0.2.10...v0.2.11) - 2020.09.29


<a name="v0.2.10"></a>
## [v0.2.10](https://github.com/hpcflow/matflow/compare/v0.2.9...v0.2.10) - 2020.09.29


<a name="v0.2.9"></a>
## [v0.2.9](https://github.com/hpcflow/matflow/compare/v0.2.8...v0.2.9) - 2020.09.17


<a name="v0.2.8"></a>
## [v0.2.8](https://github.com/hpcflow/matflow/compare/v0.2.7...v0.2.8) - 2020.09.01


<a name="v0.2.7"></a>
## [v0.2.7](https://github.com/hpcflow/matflow/compare/v0.2.6...v0.2.7) - 2020.08.18


<a name="v0.2.6"></a>
## [v0.2.6](https://github.com/hpcflow/matflow/compare/v0.2.5...v0.2.6) - 2020.07.08


<a name="v0.2.5"></a>
## [v0.2.5](https://github.com/hpcflow/matflow/compare/v0.2.4...v0.2.5) - 2020.06.27


<a name="v0.2.4"></a>
## [v0.2.4](https://github.com/hpcflow/matflow/compare/v0.2.3...v0.2.4) - 2020.06.26


<a name="v0.2.3"></a>
## [v0.2.3](https://github.com/hpcflow/matflow/compare/v0.2.2...v0.2.3) - 2020.06.26


<a name="v0.2.2"></a>
## [v0.2.2](https://github.com/hpcflow/matflow/compare/v0.2.1...v0.2.2) - 2020.06.09


<a name="v0.2.1"></a>
## [v0.2.1](https://github.com/hpcflow/matflow/compare/v0.2.0...v0.2.1) - 2020.06.09


<a name="v0.2.0"></a>
## [v0.2.0](https://github.com/hpcflow/matflow/compare/v0.1.3...v0.2.0) - 2020.06.09


<a name="v0.1.3"></a>
## [v0.1.3](https://github.com/hpcflow/matflow/compare/v0.1.2...v0.1.3) - 2020.05.27


<a name="v0.1.2"></a>
## [v0.1.2](https://github.com/hpcflow/matflow/compare/v0.1.1...v0.1.2) - 2020.05.12


<a name="v0.1.1"></a>
## [v0.1.1](https://github.com/hpcflow/matflow/compare/v0.1.0...v0.1.1) - 2020.05.07


<a name="v0.1.0"></a>
## v0.1.0 - 2020.05.07

