"""
Software Dependency Analysis Task.
This module analyzes software dependencies for version upgrades using Llama 3.3 via Groq.
"""
import json
import pandas as pd
import numpy as np
import semantic_version
import io
import csv
from dotenv import load_dotenv
from crewai import Task, Crew, Process

from document_crawler.utils.llm_config import create_agent

# Load environment variables
load_dotenv()

class DependencyAnalyzer:
    def __init__(self, master_sheet, current_versions, software_to_upgrade, target_version, criteria):
        """
        Initialize the dependency analyzer.
        
        Args:
            master_sheet (str): Path to the master dependency sheet (CSV).
            current_versions (str): Path to the current software versions (JSON).
            software_to_upgrade (str): Name of the software to upgrade.
            target_version (str): Target version for upgrade.
            criteria (str): Criteria for selecting dependent upgrades ('minimum_changes' or 'latest_available').
        """
        self.master_sheet = master_sheet
        self.current_versions_file = current_versions
        self.software_to_upgrade = software_to_upgrade
        self.target_version = target_version
        self.criteria = criteria
        
        # Load data using custom CSV parsing
        self.dependencies_df = self._load_csv_safely(master_sheet)
        
        # Load current versions
        with open(current_versions, 'r') as f:
            self.current_versions = json.load(f)
            
        # Validate input data
        self._validate_input()
    
    def _load_csv_safely(self, csv_file):
        """
        Load CSV data safely, handling common parsing issues.
        
        Args:
            csv_file (str): Path to the CSV file.
            
        Returns:
            pandas.DataFrame: The loaded CSV data.
        """
        try:
            # First try manual parsing to ensure it's clean
            rows = []
            with open(csv_file, 'r') as f:
                # Read lines and strip whitespace
                lines = [line.strip() for line in f if line.strip()]
            
            # Parse the CSV data manually
            reader = csv.reader(lines)
            header = next(reader)
            data = []
            for row in reader:
                # Ensure row has enough columns
                while len(row) < len(header):
                    row.append('')
                data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=header)
            
            # Convert Version column to string to avoid type issues
            if 'Version' in df.columns:
                df['Version'] = df['Version'].astype(str)
                
            return df
            
        except Exception as e:
            print(f"Warning: Error in manual CSV parsing: {e}")
            try:
                # Fall back to pandas with python engine
                df = pd.read_csv(csv_file, engine='python')
                
                # Convert Version column to string to avoid type issues
                if 'Version' in df.columns:
                    df['Version'] = df['Version'].astype(str)
                    
                return df
            except Exception as e2:
                print(f"Error parsing CSV with python engine: {e2}")
                # Last resort: try with skiprows
                try:
                    df = pd.read_csv(csv_file, engine='python', skiprows=0, error_bad_lines=False, warn_bad_lines=True)
                    
                    # Convert Version column to string to avoid type issues
                    if 'Version' in df.columns:
                        df['Version'] = df['Version'].astype(str)
                        
                    return df
                except Exception as e3:
                    raise ValueError(f"Failed to parse CSV file: {e3}")
    
    def _validate_input(self):
        """Validate the input data."""
        # Check if the software to upgrade exists in the master sheet
        software_exists = self.software_to_upgrade in self.dependencies_df['SoftwareName'].unique()
        if not software_exists:
            raise ValueError(f"Software '{self.software_to_upgrade}' not found in the master sheet")
        
        # Check if the target version exists in the master sheet
        target_versions = [str(v) for v in self.dependencies_df[
            self.dependencies_df['SoftwareName'] == self.software_to_upgrade
        ]['Version'].unique()]
        
        if str(self.target_version) not in target_versions:
            raise ValueError(
                f"Target version '{self.target_version}' not found for software '{self.software_to_upgrade}'. "
                f"Available versions: {', '.join(target_versions)}"
            )
        
        # Check if the software exists in the current versions
        if self.software_to_upgrade not in self.current_versions:
            raise ValueError(f"Software '{self.software_to_upgrade}' not found in current versions")
    
    def _parse_version_requirement(self, version_req):
        """
        Parse a version requirement string like '2.1+' or '>=3.0'.
        
        Args:
            version_req (str): Version requirement string.
            
        Returns:
            tuple: (operator, version) e.g., ('>=', '2.1')
        """
        # Convert numpy types to Python types
        if isinstance(version_req, (np.float64, np.float32, np.int64, np.int32)):
            version_req = str(version_req)
            
        if not version_req or pd.isna(version_req):
            # Handle empty values
            return ('==', '0.0.0')
            
        if version_req.endswith('+'):
            return ('>=', version_req[:-1])
        elif version_req.startswith('>='):
            return ('>=', version_req[2:])
        elif version_req.startswith('>'):
            return ('>', version_req[1:])
        elif version_req.startswith('=='):
            return ('==', version_req[2:])
        elif version_req.startswith('='):
            return ('==', version_req[1:])
        else:
            # Default to exact match
            return ('==', version_req)
    
    def _check_version_requirement(self, current_version, required_version):
        """
        Check if a current version meets a required version.
        
        Args:
            current_version (str): Current version string.
            required_version (str): Required version string with operator.
            
        Returns:
            bool: True if the requirement is met, False otherwise.
        """
        if not required_version or pd.isna(required_version):
            # If no requirement is specified, assume it's met
            return True
            
        operator, version = self._parse_version_requirement(required_version)
        
        try:
            current_sem = semantic_version.Version(current_version)
            required_sem = semantic_version.Version(version)
            
            if operator == '>=':
                return current_sem >= required_sem
            elif operator == '>':
                return current_sem > required_sem
            elif operator == '==':
                return current_sem == required_sem
            else:
                return False
        except ValueError:
            # Fall back to simple string comparison if semantic versioning fails
            if operator == '>=':
                return current_version >= version
            elif operator == '>':
                return current_version > version
            elif operator == '==':
                return current_version == version
            else:
                return False
    
    def _get_minimum_required_version(self, software, dependent_versions):
        """
        Get the minimum required version based on the criteria.
        
        Args:
            software (str): Software name.
            dependent_versions (list): List of required versions.
            
        Returns:
            str: The selected version based on criteria.
        """
        # Convert numpy types to Python types
        dependent_versions = [str(v) if isinstance(v, (np.float64, np.float32, np.int64, np.int32)) else v 
                              for v in dependent_versions]
        
        if self.criteria == 'minimum_changes':
            # Sort versions and find the minimum that satisfies all requirements
            all_versions = [str(v) for v in self.dependencies_df[
                self.dependencies_df['SoftwareName'] == software
            ]['Version'].unique()]
            
            # Convert to semantic versions for proper sorting
            try:
                sorted_versions = sorted(all_versions, key=lambda v: semantic_version.Version(v))
            except ValueError:
                # Fall back to string sorting if semantic versioning fails
                sorted_versions = sorted(all_versions)
            
            # Find the minimum version that satisfies all requirements
            for version in sorted_versions:
                meets_all = True
                for req_version in dependent_versions:
                    if not req_version or pd.isna(req_version):
                        continue
                    op, ver = self._parse_version_requirement(req_version)
                    try:
                        if op == '>=' and semantic_version.Version(version) < semantic_version.Version(ver):
                            meets_all = False
                            break
                    except ValueError:
                        # Fall back to string comparison
                        if op == '>=' and version < ver:
                            meets_all = False
                            break
                
                if meets_all:
                    return version
            
            # If no version satisfies all requirements, return the highest one
            return sorted_versions[-1] if sorted_versions else None
        else:  # 'latest_available'
            # Return the latest version
            all_versions = [str(v) for v in self.dependencies_df[
                self.dependencies_df['SoftwareName'] == software
            ]['Version'].unique()]
            
            try:
                sorted_versions = sorted(all_versions, key=lambda v: semantic_version.Version(v))
            except ValueError:
                sorted_versions = sorted(all_versions)
            
            return sorted_versions[-1] if sorted_versions else None
    
    def analyze(self):
        """
        Analyze dependencies and determine required upgrades.
        
        Returns:
            dict: Dictionary of required upgrades.
        """
        # Get dependencies for the target version
        dependencies = self.dependencies_df[
            (self.dependencies_df['SoftwareName'] == self.software_to_upgrade) &
            (self.dependencies_df['Version'] == str(self.target_version))
        ]
        
        required_upgrades = {}
        
        for _, row in dependencies.iterrows():
            depends_on = row['DependsOnSoftware']
            required_version = row['DependsOnVersion']
            
            # Skip if the dependency is empty or NaN
            if not depends_on or pd.isna(depends_on):
                continue
                
            # Skip if the dependency is not in current versions
            if depends_on not in self.current_versions:
                print(f"Warning: Dependency '{depends_on}' not found in current versions")
                continue
            
            current_version = self.current_versions[depends_on]
            
            # Check if the current version meets the requirement
            if not self._check_version_requirement(current_version, required_version):
                # Get all dependencies that require this software
                all_requirements = dependencies[
                    dependencies['DependsOnSoftware'] == depends_on
                ]['DependsOnVersion'].tolist()
                
                # Determine the minimum required version
                min_version = self._get_minimum_required_version(depends_on, all_requirements)
                
                required_upgrades[depends_on] = {
                    'current_version': current_version,
                    'required_version': min_version,
                    'required_by': f"{self.software_to_upgrade} {self.target_version}"
                }
        
        return required_upgrades

def run(master_sheet, current_versions_file, software_to_upgrade, target_version, criteria):
    """
    Run the software dependency analysis task.
    
    Args:
        master_sheet (str): Path to the master dependency sheet (CSV).
        current_versions_file (str): Path to the current software versions (JSON).
        software_to_upgrade (str): Name of the software to upgrade.
        target_version (str): Target version for upgrade.
        criteria (str): Criteria for selecting dependent upgrades.
    """
    print(f"Analyzing dependencies for upgrading {software_to_upgrade} to version {target_version}")
    
    try:
        # Create dependency analyzer
        analyzer = DependencyAnalyzer(
            master_sheet, 
            current_versions_file, 
            software_to_upgrade, 
            target_version, 
            criteria
        )
        
        # Analyze dependencies
        required_upgrades = analyzer.analyze()
        
        if not required_upgrades:
            print(f"No additional upgrades required to upgrade {software_to_upgrade} to version {target_version}")
        else:
            print(f"Required upgrades:")
            for software, details in required_upgrades.items():
                print(f"  - {software}: {details['current_version']} -> {details['required_version']}")
            
            print("\nDetailed upgrade information:")
            print(json.dumps(required_upgrades, indent=2))
    
    except Exception as e:
        print(f"Error analyzing dependencies: {str(e)}")

if __name__ == "__main__":
    # For testing
    run("sample_data/software_dependencies.csv", "sample_data/current_versions.json", "SoftwareA", "2.0", "minimum_changes") 