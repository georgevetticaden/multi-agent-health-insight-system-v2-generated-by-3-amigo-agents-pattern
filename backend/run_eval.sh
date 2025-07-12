#!/bin/bash

# Script to run evaluation framework with proper environment setup

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the evaluation with provided arguments
python -m evaluation.cli.run_evaluation "$@"