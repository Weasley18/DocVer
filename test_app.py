#!/usr/bin/env python3
"""
Test script for Document Crawler and Analyzer.
This script demonstrates the usage of the three main tasks using Llama 3.3 with Groq.
"""
import os
import json
from document_crawler import critical_extraction, dependency_analysis, scn_aggregation

def test_critical_extraction():
    """Test critical information extraction."""
    print("===== Testing Critical Information Extraction =====")
    
    # Ensure sample PDFs folder exists
    os.makedirs("sample_pdfs", exist_ok=True)
    
    # For actual testing, you would need to have PDF files in the sample_pdfs folder
    print("Note: This test requires PDF files in the 'sample_pdfs' folder.")
    critical_extraction.run(
        folder_path="sample_pdfs",
        fields_to_extract=["Invoice Number", "Date", "Total Amount"],
        output_file="extraction_results.csv"
    )
    print()

def test_dependency_analysis():
    """Test software dependency analysis."""
    print("===== Testing Software Dependency Analysis =====")
    dependency_analysis.run(
        master_sheet="sample_data/dependencies.csv",
        current_versions_file="sample_data/current_versions.json",
        software_to_upgrade="SoftwareA",
        target_version="2.0",
        criteria="minimum_changes"
    )
    print()

def test_scn_aggregation():
    """Test software change notice aggregation."""
    print("===== Testing Software Change Notice Aggregation =====")
    
    # Ensure sample SCNs folder exists
    os.makedirs("sample_scns", exist_ok=True)
    
    # For actual testing, you would need to have SCN PDF files in the sample_scns folder
    print("Note: This test requires SCN PDF files in the 'sample_scns' folder.")
    scn_aggregation.run(
        folder_path="sample_scns",
        software_name="SoftwareX",
        current_version="1.0",
        target_version="1.5",
        output_file="scn_results.md"
    )
    print()

if __name__ == "__main__":
    print("Document Crawler and Analyzer Test Script (using Llama 3.3 via Groq)")
    print("----------------------------------------------------------------")
    print("This script tests the three main tasks of the application.")
    print("Note: You need to set your Groq API key in the .env file.")
    print()
    
    # Check if .env file exists and has been configured
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if "your_groq_api_key_here" in content:
                print("WARNING: Please configure your Groq API key in the .env file.")
                print("You can obtain a Groq API key at https://console.groq.com/")
                print()
    else:
        print("WARNING: .env file not found. Please create one with your Groq API key.")
        print("You can obtain a Groq API key at https://console.groq.com/")
        print()
    
    # Run tests
    test_dependency_analysis()
    test_critical_extraction()
    test_scn_aggregation() 