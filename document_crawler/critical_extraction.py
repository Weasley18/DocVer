"""
Critical Information Extraction Task.
This module uses CrewAI with Llama 3.3 via Groq to extract predefined fields from PDF documents.
"""
import os
import json
import pandas as pd
from dotenv import load_dotenv
from crewai import Task, Crew, Process

from document_crawler.utils.pdf_utils import list_pdf_files, batch_extract_text
from document_crawler.utils.custom_llm import create_document_agent

# Load environment variables
load_dotenv()

def run(folder_path, fields_to_extract, output_file):
    """
    Run the critical information extraction task.
    
    Args:
        folder_path (str): Path to the folder containing PDF documents.
        fields_to_extract (list): List of fields to extract from the documents.
        output_file (str): Path to the output file (CSV or XLSX).
    """
    print(f"Starting critical information extraction from {folder_path}")
    print(f"Fields to extract: {fields_to_extract}")
    
    # Find all PDF files in the folder
    pdf_files = list_pdf_files(folder_path)
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Extract text from all PDFs
    pdf_contents = batch_extract_text(pdf_files)
    
    # Create agent using our new function that directly creates a document analyzer
    document_analyzer = create_document_agent(verbose=True, allow_delegation=False)
    
    results = []
    
    for pdf_file, text_content in pdf_contents.items():
        if not text_content.strip():
            print(f"Skipping {pdf_file} - No text content extracted")
            continue
        
        fields_str = ", ".join([f"'{field}'" for field in fields_to_extract])
        extraction_task = Task(
            description=f"""
            Extract the following fields from the document: {fields_str}.
            
            For each field:
            1. Provide comprehensive, detailed information rather than just a single line
            2. Include all relevant details from the document that pertain to each field
            3. If the field is asking for a list (e.g., "List of Issues"), extract ALL items that should be in that list
            4. For technical fields, include specific technical details, numbers, dates, and specifications
            5. If multiple sections of the document relate to a field, combine all relevant information
            6. Return 'Not Found' only if there is truly no information related to the field
            7. Format lists consistently, using numbered format (1., 2., etc.) for sequential items
            8. For dates, extract the complete date including day, month, and year if available
            9. For amounts or quantities, include units and context
            10. Structure multi-part fields logically, with clear separation between different components
            
            Return the results as a JSON dictionary where:
            - Keys are the exact field names as specified
            - Values are the extracted information as strings
            - Lists should be formatted as strings with proper numbering, not as JSON arrays
            - Keep formatting consistent and clean
            
            Document content:
            {text_content[:8000]}  # Limit content to avoid token limits
            """,
            agent=document_analyzer,
            expected_output="A comprehensive JSON dictionary with detailed extracted fields",
            output_file=None
        )
        
        # Create a crew with just this task
        extraction_crew = Crew(
            agents=[document_analyzer],
            tasks=[extraction_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Run the crew and get results
        result = extraction_crew.kickoff()
        
        # Convert CrewOutput to string if needed
        try:
            # First try to access the result content properly
            if hasattr(result, 'raw') and result.raw:
                result_str = result.raw
            elif hasattr(result, 'output') and result.output:
                result_str = result.output
            elif hasattr(result, 'content') and result.content:
                result_str = result.content
            else:
                # Fallback to string conversion
                result_str = str(result)
        except Exception as e:
            print(f"Error accessing CrewOutput content: {str(e)}")
            result_str = str(result)
        
        # Debug print to help diagnose issues
        print(f"Raw result from LLM (first 100 chars): {result_str[:100]}...")
        
        # Always save the raw output to a text file for debugging
        raw_output_dir = os.path.dirname(output_file)
        raw_output_file = os.path.join(raw_output_dir, f"raw_output_{os.path.basename(pdf_file)}.txt")
        with open(raw_output_file, "w", encoding="utf-8") as f:
            f.write(result_str)
        
        print(f"Saved raw output to {raw_output_file}")
        
        # Process the result (assuming it's a valid JSON string)
        try:
            # Parse the JSON result properly
            # First, try to find JSON in the response if it's not already in JSON format
            if not result_str.strip().startswith('{'):
                # Try to find the JSON part in the response
                start_idx = result_str.find('{')
                end_idx = result_str.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    result_str = result_str[start_idx:end_idx+1]
            
            # Handle cases where the result contains a JSON object followed by text
            if '}' in result_str and result_str.rfind('}') < len(result_str) - 1:
                # Extract just the JSON part
                result_str = result_str[:result_str.rfind('}')+1]
            
            # Special case handling: if there's a message about no data at the end,
            # it should be separated from the JSON content
            if "No data was successfully extracted" in result_str and result_str:
                print("Found both JSON data and 'No data' message - using the JSON data")
            
            # Attempt to clean up any non-JSON markup
            try:
                extracted_data = json.loads(result_str)
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError: {e}")
                # Try a more aggressive approach to find and extract JSON
                import re
                
                # First, check for common CrewAI output patterns
                # Sometimes CrewAI output is wrapped in markdown or has a prefix
                json_matches = []
                
                # Look for content in triple backticks with json
                code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', result_str)
                for block in code_blocks:
                    try:
                        extracted_data = json.loads(block.strip())
                        print("Found JSON in code block")
                        break
                    except:
                        pass
                
                # If that fails, try more generic pattern matching
                if 'extracted_data' not in locals():
                    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\}'
                    matches = re.findall(json_pattern, result_str)
                    if matches:
                        # Use the longest match as it's most likely the complete JSON
                        result_str = max(matches, key=len)
                        extracted_data = json.loads(result_str)
                    else:
                        raise
            
            # Clean and structure the extracted data
            cleaned_data = {}
            for field, value in extracted_data.items():
                # Handle lists - if content looks like a list but is a string
                if isinstance(value, str):
                    if value.strip().startswith("1.") or value.strip().startswith("-"):
                        # Format multi-line lists properly
                        cleaned_value = value.strip()
                    else:
                        # Clean up text fields
                        cleaned_value = value.strip()
                else:
                    cleaned_value = value
                
                cleaned_data[field] = cleaned_value
            
            # Add file information
            cleaned_data["File"] = os.path.basename(pdf_file)
            results.append(cleaned_data)
        except Exception as e:
            print(f"Error processing result from {pdf_file}: {str(e)}")
            print(f"Raw result: {result_str}")
    
    # Save results to CSV or Excel
    if results:
        df = pd.DataFrame(results)
        
        # Ensure 'File' column is the first column
        if 'File' in df.columns:
            cols = ['File'] + [col for col in df.columns if col != 'File']
            df = df[cols]
        
        # Store detailed structured data in JSON format as well
        json_output_file = output_file.replace('.csv', '.json').replace('.xlsx', '.json')
        with open(json_output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save to appropriate format based on file extension
        if output_file.lower().endswith('.xlsx'):
            df.to_excel(output_file, index=False)
        else:
            df.to_csv(output_file, index=False)
        
        print(f"Extraction complete. Results saved to {output_file} and {json_output_file}")
        
        # Display the raw results for debugging
        for result in results:
            print(f"Extracted from {result.get('File', 'unknown')}:")
            for field, value in result.items():
                if field != 'File':
                    print(f"  {field}: {value[:100]}..." if len(str(value)) > 100 else f"  {field}: {value}")
    else:
        print("No data was successfully extracted from the documents.")

if __name__ == "__main__":
    # For testing
    run("./sample_pdfs", ["Invoice Number", "Date", "Total Amount"], "extracted_data.csv") 