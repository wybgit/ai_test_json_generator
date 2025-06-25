#!/bin/bash

# Exit on error
set -e

echo "Cleaning previous build files..."
rm -rf build/ dist/ *.egg-info/

echo "Building wheel package..."
python setup.py bdist_wheel

echo "Wheel package created in dist/ directory:"
ls -lh dist/

echo "To install the wheel package, run:"
echo "pip install dist/$(ls dist/)" 