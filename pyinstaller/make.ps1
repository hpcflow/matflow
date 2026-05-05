# Make sure we ran one of these:
#   `poetry install`
#   `poetry install --without dev` (for building with pyinstaller and pytest)
#   `poetry install --without dev,test` (for building with pyinstaller)
# 
# Might need to disable desktop cloud sync. engines during this!
# 
param($ExeName = "matflow", $LogLevel = "INFO", $BuildType = 'onefile')
poetry run pyinstaller --log-level=$LogLevel --distpath ./dist/$BuildType --$BuildType --clean -y --name=$ExeName ..\matflow\cli.py
