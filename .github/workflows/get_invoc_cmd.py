"""Script to output the invocation command.

This is used in the test GHA workflow to check that we get the expected result.

"""

import sys
import importlib

app_import_str = sys.argv[1]
app = importlib.import_module(app_import_str)
print(app.run_time_info.invocation_command)
