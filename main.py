#!/usr/bin/env python3
"""
Document Crawler and Analyzer Application
This application uses CrewAI to orchestrate different document analysis tasks.
"""

import argparse
import os
from document_crawler import critical_extraction, dependency_analysis, scn_aggregation

def main():
    parser = argparse.ArgumentParser(description="Document Crawler and Analyzer")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Task 1: Critical Information Extraction
    extract_parser = subparsers.add_parser("extract", help="Extract critical information from PDFs")
    extract_parser.add_argument("--folder", required=True, help="Path to folder containing PDF documents")
    extract_parser.add_argument("--fields", required=True, nargs="+", help="Fields to extract (e.g., 'Invoice Number' 'Date')")
    extract_parser.add_argument("--output", default="extracted_data.csv", help="Output file path (CSV or XLSX)")
    
    # Task 2: Software Dependency Analysis
    dependency_parser = subparsers.add_parser("analyze-deps", help="Analyze software dependencies")
    dependency_parser.add_argument("--master-sheet", required=True, help="Path to master dependency sheet (CSV)")
    dependency_parser.add_argument("--current", required=True, help="Path to current software versions (JSON)")
    dependency_parser.add_argument("--software", required=True, help="Name of software to upgrade")
    dependency_parser.add_argument("--target-version", required=True, help="Target version for upgrade")
    dependency_parser.add_argument("--criteria", default="minimum_changes", 
                                  choices=["minimum_changes", "latest_available"],
                                  help="Criteria for selecting dependent upgrades")
    
    # Task 3: Software Change Notice Aggregation
    scn_parser = subparsers.add_parser("aggregate-scn", help="Aggregate Software Change Notices")
    scn_parser.add_argument("--folder", required=True, help="Path to folder containing SCN PDFs")
    scn_parser.add_argument("--software", required=True, help="Software name")
    scn_parser.add_argument("--current-version", required=True, help="Current installed version")
    scn_parser.add_argument("--target-version", required=True, help="Target upgrade version")
    scn_parser.add_argument("--output", default="aggregated_scn.md", help="Output file path (CSV or MD)")
    
    args = parser.parse_args()
    
    if args.command == "extract":
        critical_extraction.run(args.folder, args.fields, args.output)
    elif args.command == "analyze-deps":
        dependency_analysis.run(args.master_sheet, args.current, args.software, 
                              args.target_version, args.criteria)
    elif args.command == "aggregate-scn":
        scn_aggregation.run(args.folder, args.software, args.current_version, 
                          args.target_version, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 