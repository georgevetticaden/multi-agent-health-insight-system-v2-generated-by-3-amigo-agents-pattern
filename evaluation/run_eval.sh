#!/bin/bash

# Script to run evaluation framework with proper environment setup

# Navigate to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

# Set PYTHONPATH to include backend and project root
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/backend"

# Run the evaluation with provided arguments
python -m evaluation.cli.run_evaluation "$@"