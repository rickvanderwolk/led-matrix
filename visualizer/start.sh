#!/bin/bash

# LED Matrix Visualizer - Quick Start Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment niet gevonden!"
    echo "Voer eerst ./visualizer/install.sh uit om te installeren."
    exit 1
fi

# Activate virtual environment and run
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/run_mode.py" "$@"
