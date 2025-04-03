#!/usr/bin/env python3
"""
Script to create sample PDF files for demonstration purposes.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def text_to_pdf(text_file, pdf_file):
    """Convert a text file to PDF."""
    print(f"Converting {text_file} to {pdf_file}")
    
    # Create a canvas
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    
    # Set font and size
    c.setFont("Courier", 10)
    
    # Read the text file
    with open(text_file, 'r') as f:
        text_content = f.readlines()
    
    # Set the initial y position
    y = height - inch
    
    # Add text line by line
    for line in text_content:
        if y < inch:
            c.showPage()
            y = height - inch
            c.setFont("Courier", 10)
        
        c.drawString(inch, y, line.rstrip())
        y -= 14  # Line spacing
    
    # Save the PDF
    c.save()
    print(f"Created {pdf_file}")

def create_sample_pdfs():
    """Create sample PDFs from text files."""
    # Create sample directories if they don't exist
    os.makedirs("sample_pdfs", exist_ok=True)
    os.makedirs("sample_scns", exist_ok=True)
    
    # Convert invoice to PDF
    invoice_text = "sample_data/demo_invoice.txt"
    invoice_pdf = "sample_pdfs/invoice_2023_0042.pdf"
    if os.path.exists(invoice_text):
        text_to_pdf(invoice_text, invoice_pdf)
    else:
        print(f"Error: {invoice_text} not found")
    
    # Convert SCN to PDF
    scn_text = "sample_data/SoftwareX_SCN.txt"
    scn_pdf = "sample_scns/SoftwareX_v1.2_SCN.pdf"
    if os.path.exists(scn_text):
        text_to_pdf(scn_text, scn_pdf)
    else:
        print(f"Error: {scn_text} not found")
    
    # Create another SCN for a different version for demonstration
    create_another_scn()

def create_another_scn():
    """Create another SCN for a different version."""
    scn_content = """SOFTWARE CHANGE NOTICE
=============================

Software: SoftwareX
Version: 1.3
Release Date: June 15, 2023
Previous Version: 1.2

=============================
NEW FEATURES
=============================

1. Real-time Collaboration: Added multi-user editing capabilities.
2. Custom Dashboard Builder: New drag-and-drop dashboard customization.
3. Enhanced Analytics: Improved data visualization with interactive charts.
4. Mobile Application: Released companion mobile app for iOS and Android.
5. Automated Workflow Engine: Added customizable workflow automation tools.

=============================
RESOLVED ISSUES
=============================

1. Fixed PDF exports formatting issues with complex tables.
2. Improved dashboard widget loading performance on low-bandwidth connections.
3. Automated reconnection for third-party integrations after updates.
4. Optimized database queries for large datasets exceeding 1 million records.
5. Corrected calculation errors in the forecasting module.

=============================
KNOWN ISSUES
=============================

1. Occasional disconnections in real-time collaboration with more than 20 users.
2. Mobile app may experience battery drain on older devices.
3. Some custom dashboard widgets require manual refresh after data updates.
4. Limited offline functionality in the mobile application.

=============================
SYSTEM REQUIREMENTS
=============================

- Operating System: Windows 10+, macOS 11+, or Linux (kernel 5.4+)
- RAM: Minimum 8GB, Recommended 16GB
- Storage: 750MB free space
- Dependencies: .NET Runtime 6.0 or higher

=============================
INSTALLATION INSTRUCTIONS
=============================

1. Backup your existing configuration.
2. Download the update package from the customer portal.
3. Run the installer and follow the on-screen instructions.
4. Restart the application after installation.

For detailed instructions, please refer to the Documentation Portal.
"""
    
    # Create the text file
    scn_text = "sample_data/SoftwareX_SCN_v1.3.txt"
    with open(scn_text, 'w') as f:
        f.write(scn_content)
    
    # Convert to PDF
    scn_pdf = "sample_scns/SoftwareX_v1.3_SCN.pdf"
    text_to_pdf(scn_text, scn_pdf)

if __name__ == "__main__":
    # Check if reportlab is installed
    try:
        import reportlab
    except ImportError:
        print("Error: ReportLab is not installed. Please install it using:")
        print("pip install reportlab")
        sys.exit(1)
    
    create_sample_pdfs()
    print("Sample PDFs created successfully!")
    print("You can now use them with the Streamlit application.") 