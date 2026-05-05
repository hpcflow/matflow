Template components
-------------------

How to name parameters and task schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameter type names (i.e. the `typ` attribute) must be valid Python identifiers. This means 
that they cannot start with a number. They must also be fully alphanumeric, but may include 
underscores (but not at the start). These rules also apply to task schema methods,
implementations, and objective names. See :func:`hpcflow.sdk.core.utils.check_valid_py_identifier`
for more details. By convention, lower case is preferred, except for acronyms and
initialisms.
