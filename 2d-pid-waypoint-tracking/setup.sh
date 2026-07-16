#!/usr/bin/env bash

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
else
  echo "Virtual environment already exists."
fi

# Activate venv (cross-platform)
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi

# Upgrade pip + install in editable mode
pip install --upgrade pip
pip install -e .

echo "Setup complete."
