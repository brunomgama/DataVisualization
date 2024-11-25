#!/bin/bash

# Navigate to the directory
cd "/Users/brunogama/Documents/Data Visualization/untitled/lambda" || exit

# Remove existing zip file if it exists
rm -f file_checker.zip

# Create a new zip file containing the file_checker.py
zip -r file_checker.zip file_checker.py

# Output success message
echo "file_checker.zip created successfully!"
