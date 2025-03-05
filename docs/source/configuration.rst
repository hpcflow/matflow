:orphan:

.. _config:

.. jinja:: first_ctx

    #############
    Configuration
    #############

    MatFlow uses a config file to control details of how it executes workflows.
    A :ref:`default config file <default_config>` will be created the first time you submit a workflow.
    This will work without modification on a personal machine,
    however if you are using MatFlow on HPC you will likely need to make some 
    modifications to describe the job scheduler, and settings for multiple cores,
    and to point to your MatFlow environments file.
    
    `Some examples <https://github.com/hpcflow/matflow-configs>`_ are given 
    for the University of Manchester's CSF.
