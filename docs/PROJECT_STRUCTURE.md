# AI JSON Generator Project Structure

This document explains the structure of the AI JSON Generator project and how to clean up and package it.

## Project Structure

After running the cleaning script (`clean_project.sh`), the project will have the following structure:

```
AI_JSON_Generator/
├── ai_json_generator/         # Main package directory
│   ├── __init__.py            # Package initialization
│   ├── config.json            # Default configuration
│   ├── generate_json.py       # Core JSON generation functionality
│   ├── generate_operator_testcase.py  # Operator test case generation
│   ├── data_files/            # Data files used by the generator
│   └── prompts/               # Prompt templates
│
├── backup/                    # Backup of original files (after cleaning)
├── build_wheel.sh             # Script to build wheel package
├── clean_project.sh           # Script to clean up and organize files
├── install_and_test.sh        # Script to install and test the package
├── LICENSE                    # License file
├── MANIFEST.in                # Manifest file for package data
├── PROJECT_STRUCTURE.md       # This file
├── README.md                  # Main documentation
└── setup.py                   # Package setup configuration
```

## Workflow for Cleaning and Packaging

1. Clean the project structure:
   ```bash
   ./clean_project.sh
   ```
   This moves duplicate files to the backup directory, leaving only the package and build-related files.

2. Build the wheel package:
   ```bash
   ./build_wheel.sh
   ```
   This creates a wheel package in the `dist/` directory.

3. Install and test the package:
   ```bash
   ./install_and_test.sh
   ```
   This installs the package in development mode and runs a test.

## Configuration Files

The package can be configured using a `config.json` file, which can be located in multiple places:

1. Path specified by the `AI_JSON_GENERATOR_CONFIG` environment variable
2. Path provided as a command-line argument
3. Current working directory
4. Package installation directory
5. User's home directory at `~/.ai_json_generator/config.json`

## Package Data

The package includes the following data:
- Prompt templates in the `prompts/` directory
- Data files in the `data_files/` directory
- Default configuration in `config.json`

These files are included in the package distribution via the `MANIFEST.in` file and `package_data` in `setup.py`. 