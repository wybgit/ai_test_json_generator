#!/bin/bash

# Exit on error
set -e

echo "Cleaning project structure..."

# Create a backup directory for original files that will be removed
mkdir -p backup

# Move duplicate files to backup
echo "Moving original files to backup directory..."

# Move core functionality files if they exist in root
for file in generate_json.py generate_operator_testcase.py; do
    if [ -f "$file" ]; then
        echo "Moving $file to backup/"
        mv "$file" backup/
    fi
done

# Move the batch_generate_testcases.py file to backup if it exists
if [ -f "batch_generate_testcases.py" ]; then
    echo "Moving batch_generate_testcases.py to backup/"
    mv batch_generate_testcases.py backup/
fi

# Move data directories to backup if they're in the root directory
# We'll keep only those in the ai_json_generator directory
for dir in prompts data_files; do
    if [ -d "$dir" ] && [ "$dir" != "ai_json_generator/$dir" ]; then
        echo "Moving $dir to backup/"
        mv "$dir" backup/
    fi
done

echo "Project cleanup complete. Original files backed up to backup/"
echo "The ai_json_generator package directory and packaging files remain in the root."
echo ""
echo "Files remaining in root directory:"
ls -l | grep -v "backup" | grep -v "^d" | awk '{print $9}'
echo ""
echo "Directories remaining in root directory:"
ls -ld */ | grep -v "backup" | awk '{print $9}' 