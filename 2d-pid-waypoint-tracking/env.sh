#!/usr/bin/env bash

# Ensure venv exists
if [ ! -d ".venv" ]; then
  echo "No virtual environment found. Run ./setup.sh first."
  exit 1
fi

# Activate venv (cross-platform)
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi

# Set PYTHONPATH to src/
export PYTHONPATH=$(pwd)/src
echo "Environment activated. PYTHONPATH=$PYTHONPATH"

