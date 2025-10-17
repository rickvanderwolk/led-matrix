#!/bin/bash

# LED Matrix Visualizer - Installation Script

echo "LED Matrix Visualizer - Installatie"
echo "===================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment already exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment bestaat al in: $VENV_DIR"
    read -p "Wil je de bestaande environment verwijderen en opnieuw installeren? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Verwijderen van bestaande environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Installatie geannuleerd."
        exit 0
    fi
fi

# Create virtual environment
echo "Aanmaken van virtual environment..."
python3 -m venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    echo "Fout: Kon geen virtual environment aanmaken."
    echo "Zorg ervoor dat python3-venv is geïnstalleerd."
    exit 1
fi

# Activate virtual environment
echo "Activeren van virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgraden van pip..."
pip install --upgrade pip

# Install requirements
echo "Installeren van dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

if [ $? -ne 0 ]; then
    echo "Fout: Kon dependencies niet installeren."
    exit 1
fi

echo ""
echo "✓ Installatie succesvol!"
echo ""
echo "Om de visualizer te gebruiken:"
echo "  1. Activeer de virtual environment:"
echo "     source visualizer/venv/bin/activate"
echo ""
echo "  2. Start de visualizer:"
echo "     python visualizer/run_mode.py"
echo ""
echo "Voor meer informatie, zie: visualizer/README.md"
