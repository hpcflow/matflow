:: Re-run sphinx-apidoc to re-write the stub files for reference documentation
:: Note: this will overwrite customisations to these files
:: TODO: in future, might want to incorporate customisations
sphinx-apidoc.exe --force --output-dir .\source\reference ..
