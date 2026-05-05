# Make sure we ran one of these:
#   `poetry install`
#   `poetry install --without dev` (for building with pyinstaller and pytest)
#   `poetry install --without dev,test` (for building with pyinstaller)
# 
# Might need to disable desktop cloud sync. engines during this!
# 
EXE_NAME_DEFAULT="matflow"
LOG_LEVEL_DEFAULT="INFO"
BUILD_TYPE_DEFAULT="onefile"
EXE_NAME="${1:-$EXE_NAME_DEFAULT}"
LOG_LEVEL="${2:-$LOG_LEVEL_DEFAULT}"
BUILD_TYPE="${3:-$BUILD_TYPE_DEFAULT}"
poetry run pyinstaller --log-level=$LOG_LEVEL --distpath ./dist/$BUILD_TYPE --$BUILD_TYPE --clean -y --name=$EXE_NAME ../matflow/cli.py
