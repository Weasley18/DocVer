#!/usr/bin/env python3
"""
Test script to diagnose CSV parsing issues.
"""
import pandas as pd
import os

def test_csv_parsing(file_path):
    """Test CSV parsing."""
    print(f"Testing CSV parsing for {file_path}...")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    
    # Try to read with different parsers
    try:
        # Read with pandas and 'python' engine
        df_python = pd.read_csv(file_path, engine='python')
        print(f"Successfully read file with 'python' engine. Found {len(df_python)} rows.")
        print("Headers:", df_python.columns.tolist())
        print("First row:", df_python.iloc[0].tolist())
    except Exception as e:
        print(f"Error reading with 'python' engine: {str(e)}")
    
    try:
        # Read with pandas and 'c' engine (default)
        df_c = pd.read_csv(file_path, engine='c')
        print(f"Successfully read file with 'c' engine. Found {len(df_c)} rows.")
        print("Headers:", df_c.columns.tolist())
        print("First row:", df_c.iloc[0].tolist())
    except Exception as e:
        print(f"Error reading with 'c' engine: {str(e)}")
    
    # Read file as text to check content
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        print(f"File has {len(lines)} lines.")
        print("Line by line content:")
        for i, line in enumerate(lines):
            print(f"Line {i+1}: {repr(line)}")
    except Exception as e:
        print(f"Error reading file as text: {str(e)}")

if __name__ == "__main__":
    # Test the sample dependencies.csv file
    test_csv_parsing("sample_data/dependencies.csv") 