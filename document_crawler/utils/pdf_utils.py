"""
Utility functions for PDF processing.
"""
import os
import PyPDF2
from tqdm import tqdm

def list_pdf_files(folder_path):
    """
    List all PDF files in a folder.
    
    Args:
        folder_path (str): Path to the folder containing PDF files.
        
    Returns:
        list: List of paths to PDF files.
    """
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text content.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {str(e)}")
        return ""

def batch_extract_text(pdf_files):
    """
    Extract text from multiple PDF files.
    
    Args:
        pdf_files (list): List of paths to PDF files.
        
    Returns:
        dict: Dictionary mapping file paths to extracted text.
    """
    results = {}
    for pdf_file in tqdm(pdf_files, desc="Extracting text from PDFs"):
        text = extract_text_from_pdf(pdf_file)
        results[pdf_file] = text
    return results

def parse_version_from_filename(filename, software_name):
    """
    Extract version number from a filename.
    
    Args:
        filename (str): Name of the file.
        software_name (str): Name of the software.
        
    Returns:
        str: Extracted version or None if not found.
    """
    # Remove file extension and path
    base_name = os.path.basename(filename)
    file_name_no_ext = os.path.splitext(base_name)[0]
    
    # Try common patterns for version extraction
    # Pattern: SoftwareX_v1.1_SCN.pdf
    if software_name in file_name_no_ext:
        parts = file_name_no_ext.split('_')
        for part in parts:
            if part.startswith('v') and '.' in part[1:]:
                return part[1:]  # Remove 'v' prefix
            
            # Try to find a part that looks like a version (contains digits and dots)
            if any(c.isdigit() for c in part) and '.' in part:
                return part
    
    return None 