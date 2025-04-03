"""
Software Change Notice Aggregation Task.
This module aggregates software change notices between versions using Llama 3.3 via Groq.
"""
import os
import json
import pandas as pd
from dotenv import load_dotenv
from crewai import Task, Crew, Process
import semantic_version

from document_crawler.utils.pdf_utils import list_pdf_files, extract_text_from_pdf, parse_version_from_filename
from document_crawler.utils.llm_config import create_agent

# Load environment variables
load_dotenv()

def run(folder_path, software_name, current_version, target_version, output_file):
    """
    Run the software change notice aggregation task.
    
    Args:
        folder_path (str): Path to the folder containing SCN PDFs.
        software_name (str): Name of the software.
        current_version (str): Current installed version.
        target_version (str): Target upgrade version.
        output_file (str): Path to the output file (CSV or MD).
    """
    print(f"Aggregating SCNs for {software_name} from version {current_version} to {target_version}")
    
    # Find all PDF files in the folder
    pdf_files = list_pdf_files(folder_path)
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    # Filter PDFs by software name and version range
    relevant_pdfs = []
    for pdf_file in pdf_files:
        version = parse_version_from_filename(pdf_file, software_name)
        if version:
            try:
                # Try to parse as semantic version
                ver_sem = semantic_version.Version(version)
                curr_sem = semantic_version.Version(current_version)
                target_sem = semantic_version.Version(target_version)
                
                # Include if version is between current (exclusive) and target (inclusive)
                if curr_sem < ver_sem <= target_sem:
                    relevant_pdfs.append((pdf_file, version))
            except ValueError:
                # Fall back to string comparison
                if current_version < version <= target_version:
                    relevant_pdfs.append((pdf_file, version))
    
    if not relevant_pdfs:
        print(f"No relevant SCN PDFs found for {software_name} between versions {current_version} and {target_version}")
        return
    
    # Sort PDFs by version
    try:
        relevant_pdfs.sort(key=lambda x: semantic_version.Version(x[1]))
    except ValueError:
        relevant_pdfs.sort(key=lambda x: x[1])
    
    print(f"Found {len(relevant_pdfs)} relevant SCN PDFs")
    
    # Create agent with Llama 3.3
    scn_analyzer = create_agent(
        role="SCN Analyzer",
        goal="Extract and categorize information from Software Change Notices",
        backstory="You are an expert at analyzing software change notices and extracting key information."
    )
    
    # Process each SCN PDF
    new_features_all = []
    resolved_issues_all = []
    known_issues_all = []
    
    for pdf_file, version in relevant_pdfs:
        print(f"Processing SCN for version {version}...")
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(pdf_file)
        if not text_content.strip():
            print(f"Skipping {pdf_file} - No text content extracted")
            continue
        
        # Create task for this SCN
        scn_task = Task(
            description=f"""
            Analyze the Software Change Notice (SCN) for {software_name} version {version}.
            
            Extract the following information:
            1. New Features: List of new features introduced in this version.
            2. Resolved Issues: List of issues that were fixed in this version.
            3. Known Issues: List of known issues mentioned in this version.
            
            Return the results as a JSON dictionary with three keys:
            "new_features", "resolved_issues", and "known_issues", each containing a list of items.
            
            Document content:
            {text_content[:8000]}  # Limit content to avoid token limits
            """,
            agent=scn_analyzer,
            expected_output="A JSON dictionary with extracted lists",
            output_file=None
        )
        
        # Create a crew with just this task
        scn_crew = Crew(
            agents=[scn_analyzer],
            tasks=[scn_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Run the crew and get results
        result = scn_crew.kickoff()
        
        # Process the result
        try:
            # Parse the JSON result properly
            # First, try to find JSON in the response if it's not already in JSON format
            result_str = result
            if not result_str.strip().startswith('{'):
                # Try to find the JSON part in the response
                start_idx = result_str.find('{')
                end_idx = result_str.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    result_str = result_str[start_idx:end_idx+1]
            
            extracted_data = json.loads(result_str)
            
            # Add version information to each item
            new_features = [{"feature": item, "version": version} for item in extracted_data.get("new_features", [])]
            resolved_issues = [{"issue": item, "version": version} for item in extracted_data.get("resolved_issues", [])]
            known_issues = [{"issue": item, "version": version} for item in extracted_data.get("known_issues", [])]
            
            new_features_all.extend(new_features)
            resolved_issues_all.extend(resolved_issues)
            known_issues_all.extend(known_issues)
            
        except Exception as e:
            print(f"Error processing result from {pdf_file}: {str(e)}")
            print(f"Raw result: {result}")
    
    # Deduplicate entries and reconcile issues
    new_features_deduped = _deduplicate_by_text(new_features_all, "feature")
    resolved_issues_deduped = _deduplicate_by_text(resolved_issues_all, "issue")
    
    # Remove any issue from known_issues if it appears in resolved_issues
    remaining_known_issues = _reconcile_issues(known_issues_all, resolved_issues_deduped)
    
    # Save results
    results = {
        "software": software_name,
        "current_version": current_version,
        "target_version": target_version,
        "new_features": new_features_deduped,
        "resolved_issues": resolved_issues_deduped,
        "remaining_known_issues": remaining_known_issues
    }
    
    if output_file.lower().endswith('.md'):
        _save_to_markdown(results, output_file)
    else:
        _save_to_csv(results, output_file)
    
    print(f"SCN aggregation complete. Results saved to {output_file}")

def _deduplicate_by_text(items, text_key):
    """
    Deduplicate items by text content.
    
    Args:
        items (list): List of dictionaries.
        text_key (str): Key for the text content.
        
    Returns:
        list: Deduplicated list.
    """
    seen = set()
    deduped = []
    
    for item in items:
        text = item[text_key].lower().strip()
        if text not in seen:
            seen.add(text)
            deduped.append(item)
    
    return deduped

def _reconcile_issues(known_issues, resolved_issues):
    """
    Remove any issue from known_issues if it appears in resolved_issues.
    
    Args:
        known_issues (list): List of known issues dictionaries.
        resolved_issues (list): List of resolved issues dictionaries.
        
    Returns:
        list: Reconciled known issues list.
    """
    # Create a set of resolved issues text
    resolved_set = {item["issue"].lower().strip() for item in resolved_issues}
    
    # Filter out known issues that have been resolved
    remaining_issues = []
    for issue in known_issues:
        text = issue["issue"].lower().strip()
        if text not in resolved_set:
            remaining_issues.append(issue)
    
    return remaining_issues

def _save_to_markdown(results, output_file):
    """
    Save results to a Markdown file.
    
    Args:
        results (dict): Results dictionary.
        output_file (str): Output file path.
    """
    with open(output_file, 'w') as f:
        f.write(f"# Software Change Notice Aggregation for {results['software']}\n\n")
        f.write(f"Upgrade from version {results['current_version']} to {results['target_version']}\n\n")
        
        f.write("## New Features\n\n")
        for item in results["new_features"]:
            f.write(f"- {item['feature']} (v{item['version']})\n")
        
        f.write("\n## Resolved Issues\n\n")
        for item in results["resolved_issues"]:
            f.write(f"- {item['issue']} (v{item['version']})\n")
        
        f.write("\n## Remaining Known Issues\n\n")
        for item in results["remaining_known_issues"]:
            f.write(f"- {item['issue']} (v{item['version']})\n")

def _save_to_csv(results, output_file):
    """
    Save results to CSV files.
    
    Args:
        results (dict): Results dictionary.
        output_file (str): Output file path.
    """
    # Create DataFrames for each category
    df_features = pd.DataFrame(results["new_features"])
    df_resolved = pd.DataFrame(results["resolved_issues"])
    df_known = pd.DataFrame(results["remaining_known_issues"])
    
    # Add category column to each DataFrame
    if not df_features.empty:
        df_features["category"] = "New Feature"
    if not df_resolved.empty:
        df_resolved["category"] = "Resolved Issue"
    if not df_known.empty:
        df_known["category"] = "Known Issue"
    
    # Combine DataFrames
    df_combined = pd.concat([df_features, df_resolved, df_known], ignore_index=True)
    
    # Add metadata columns
    df_combined["software"] = results["software"]
    df_combined["current_version"] = results["current_version"]
    df_combined["target_version"] = results["target_version"]
    
    # Save to CSV
    df_combined.to_csv(output_file, index=False)

if __name__ == "__main__":
    # For testing
    run("./sample_scns", "SoftwareX", "1.0", "1.5", "aggregated_scn.md") 