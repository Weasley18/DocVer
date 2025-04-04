#!/usr/bin/env python3
"""
Streamlit web interface for Document Crawler and Analyzer.
"""
import os
import json
import tempfile
import pandas as pd
import streamlit as st
from document_crawler import critical_extraction, dependency_analysis, scn_aggregation

# Set page configuration
st.set_page_config(
    page_title="Document Crawler and Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Main title
st.title("Document Crawler and Analyzer")
st.markdown("Using Llama 3.3 via Groq")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a feature:",
    ["Home", "Critical Information Extraction", "Software Dependency Analysis", "Software Change Notice Aggregation"]
)

# Home page
if page == "Home":
    st.header("Welcome to Document Crawler and Analyzer")
    st.markdown("""
    This application uses CrewAI with Llama 3.3 (via Groq) to orchestrate document analysis tasks. 
    It provides functionality for:
    
    1. **Critical Information Extraction** - Extract predefined fields from PDF documents
    2. **Software Dependency Analysis** - Analyze software dependencies for version upgrades
    3. **Software Change Notice Aggregation** - Aggregate change notices between software versions
    
    Select a feature from the sidebar to get started.
    """)
    
    # Display API key status
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        st.success("✅ Groq API key is configured")
    else:
        st.error("❌ Groq API key is not configured. Please check your .env file.")

# Critical Information Extraction
elif page == "Critical Information Extraction":
    st.header("Critical Information Extraction")
    st.markdown("""
    This feature extracts predefined fields from PDF documents using AI.
    
    Upload your PDF files and specify the fields you want to extract.
    """)
    
    # File uploader for PDFs
    uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", accept_multiple_files=True)
    
    # Field specification
    fields_input = st.text_input(
        "Fields to extract (comma-separated)",
        placeholder="e.g., Invoice Number, Date, Total Amount",
        help="Enter the fields you want to extract from the documents, separated by commas."
    )
    
    if uploaded_files and fields_input:
        fields = [field.strip() for field in fields_input.split(",")]
        
        if st.button("Extract Information", type="primary"):
            with st.spinner("Extracting information from PDFs..."):
                # Create a temporary directory to save the uploaded files
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files to the temporary directory
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    
                    # Create a temporary output file
                    output_file = os.path.join(temp_dir, "extracted_data.csv")
                    
                    # Run the extraction
                    critical_extraction.run(temp_dir, fields, output_file)
                    
                    # Display the results
                    if os.path.exists(output_file):
                        try:
                            df = pd.read_csv(output_file)
                            
                            # Check if we have any data
                            if len(df) > 0:
                                st.success(f"Successfully extracted information from {len(uploaded_files)} documents.")
                                
                                # Create tabs for different view modes
                                tab1, tab2, tab3 = st.tabs(["Table View", "Document View", "JSON View"])
                                
                                with tab1:
                                    # Table view (improved dataframe display)
                                    st.subheader("Extracted Data - Table Format")
                                    st.dataframe(
                                        df,
                                        use_container_width=True,
                                        column_config={
                                            "File": st.column_config.TextColumn("Document", width="medium"),
                                            **{field: st.column_config.TextColumn(field, width="large") for field in fields}
                                        }
                                    )
                                
                                with tab2:
                                    # Document-centric view
                                    st.subheader("Extracted Data - By Document")
                                    for doc_file in df["File"].unique():
                                        doc_data = df[df["File"] == doc_file]
                                        with st.expander(f"📄 {doc_file}"):
                                            for field in fields:
                                                if field in doc_data.columns:
                                                    field_value = doc_data[field].values[0]
                                                    st.markdown(f"**{field}**")
                                                    st.markdown(f"{field_value}")
                                                    st.divider()
                                
                                with tab3:
                                    # JSON view
                                    st.subheader("Extracted Data - JSON Format")
                                    # Convert to JSON with document filenames as keys
                                    json_data = {}
                                    for doc_file in df["File"].unique():
                                        doc_data = df[df["File"] == doc_file].iloc[0].to_dict()
                                        json_data[doc_file] = {k: v for k, v in doc_data.items() if k != "File"}
                                    
                                    st.json(json_data)
                                
                                # Download options
                                st.subheader("Download Options")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    # CSV download
                                    with open(output_file, "rb") as file:
                                        st.download_button(
                                            label="Download CSV",
                                            data=file,
                                            file_name="extracted_data.csv",
                                            mime="text/csv",
                                        )
                                
                                with col2:
                                    # JSON download
                                    json_str = json.dumps(json_data, indent=2)
                                    st.download_button(
                                        label="Download JSON",
                                        data=json_str,
                                        file_name="extracted_data.json",
                                        mime="application/json",
                                    )
                            else:
                                # Try to load from JSON if CSV is empty
                                json_output_file = output_file.replace('.csv', '.json')
                                if os.path.exists(json_output_file):
                                    try:
                                        with open(json_output_file, 'r') as f:
                                            json_data = json.load(f)
                                        
                                        if json_data:
                                            st.success(f"Successfully extracted information from {len(uploaded_files)} documents.")
                                            st.subheader("Extracted Data - JSON Format")
                                            st.json(json_data)
                                            
                                            # Convert JSON to DataFrame for download
                                            df = pd.DataFrame(json_data)
                                            
                                            # Download options
                                            st.subheader("Download Options")
                                            json_str = json.dumps(json_data, indent=2)
                                            st.download_button(
                                                label="Download JSON",
                                                data=json_str,
                                                file_name="extracted_data.json",
                                                mime="application/json",
                                            )
                                        else:
                                            # Check for raw output files
                                            raw_files = [f for f in os.listdir(temp_dir) if f.startswith("raw_output_")]
                                            if raw_files:
                                                st.subheader("Raw Extraction Results")
                                                st.info("Showing raw extraction results:")
                                                
                                                for raw_file in raw_files:
                                                    with st.expander(f"Raw data from: {raw_file.replace('raw_output_', '')}"):
                                                        try:
                                                            with open(os.path.join(temp_dir, raw_file), 'r', encoding='utf-8') as f:
                                                                raw_content = f.read()
                                                            
                                                            # Check if content contains a "List of Issues" section
                                                            if "List of Issues" in raw_content or "list of issues" in raw_content.lower():
                                                                st.markdown("### Extracted List of Issues:")
                                                                # Try to find and format the list content
                                                                import re
                                                                list_section = re.search(r'"List of Issues"\s*:\s*"(.*?)"(?:,|\})', raw_content, re.DOTALL | re.IGNORECASE)
                                                                if list_section:
                                                                    issues_content = list_section.group(1).replace('\\n', '\n').replace('\\"', '"')
                                                                    st.markdown(issues_content)
                                                                else:
                                                                    st.text(raw_content)
                                                            else:
                                                                # Try to extract JSON part
                                                                import re
                                                                json_match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
                                                                if json_match:
                                                                    try:
                                                                        json_data = json.loads(json_match.group(1))
                                                                        st.json(json_data)
                                                                    except Exception:
                                                                        st.text(raw_content)
                                                                else:
                                                                    st.text(raw_content)
                                                        except Exception as file_error:
                                                            st.error(f"Error reading raw file: {str(file_error)}")
                                            else:
                                                st.warning("No data was extracted from the documents.")
                                    except Exception as e:
                                        st.warning(f"Could not parse JSON results: {str(e)}")
                                        
                                        # Try raw files as a fallback
                                        raw_files = [f for f in os.listdir(temp_dir) if f.startswith("raw_output_")]
                                        if raw_files:
                                            st.subheader("Raw Extraction Results")
                                            st.info("Showing raw extraction results as fallback:")
                                            
                                            for raw_file in raw_files:
                                                with st.expander(f"Raw data from: {raw_file.replace('raw_output_', '')}"):
                                                    try:
                                                        with open(os.path.join(temp_dir, raw_file), 'r', encoding='utf-8') as f:
                                                            st.text(f.read())
                                                    except Exception as file_error:
                                                        st.error(f"Error reading raw file: {str(file_error)}")
                                else:
                                    # Check for raw output files
                                    raw_files = [f for f in os.listdir(temp_dir) if f.startswith("raw_output_")]
                                    if raw_files:
                                        st.subheader("Raw Extraction Results")
                                        st.info("Showing raw extraction results:")
                                        
                                        for raw_file in raw_files:
                                            with st.expander(f"Raw data from: {raw_file.replace('raw_output_', '')}"):
                                                try:
                                                    with open(os.path.join(temp_dir, raw_file), 'r', encoding='utf-8') as f:
                                                        st.text(f.read())
                                                except Exception as file_error:
                                                    st.error(f"Error reading raw file: {str(file_error)}")
                                    else:
                                        st.warning("No data was extracted from the documents.")
                        except Exception as e:
                            st.warning(f"Could not parse detailed results: {str(e)}")
                            
                            # Show raw output files if available
                            raw_files = [f for f in os.listdir(temp_dir) if f.startswith("raw_output_")]
                            if raw_files:
                                st.subheader("Raw Extraction Results")
                                st.info("The structured data couldn't be parsed, but here are the raw extraction results:")
                                
                                for raw_file in raw_files:
                                    with st.expander(f"Raw data from: {raw_file.replace('raw_output_', '')}"):
                                        try:
                                            with open(os.path.join(temp_dir, raw_file), 'r', encoding='utf-8') as f:
                                                st.text(f.read())
                                        except Exception as file_error:
                                            st.error(f"Error reading raw file: {str(file_error)}")
                    else:
                        st.error("Failed to extract information from the documents.")

# Software Dependency Analysis
elif page == "Software Dependency Analysis":
    st.header("Software Dependency Analysis")
    st.markdown("""
    This feature analyzes software dependencies for version upgrades.
    
    Upload your master dependency sheet (CSV) and current software versions (JSON).
    """)
    
    # Option to use sample data
    use_sample_data = st.checkbox("Use sample data for testing", help="Use built-in sample data instead of uploading files")
    
    if not use_sample_data:
        col1, col2 = st.columns(2)
        
        with col1:
            # Upload master dependency sheet
            master_sheet_file = st.file_uploader("Upload master dependency sheet", type="csv")
            
            # Display example format
            with st.expander("Example master dependency sheet format"):
                st.code("""
SoftwareName,Version,DependsOnSoftware,DependsOnVersion
SoftwareA,2.0,SoftwareB,2.1+
SoftwareA,2.0,SoftwareC,3.5+
SoftwareB,2.1,SoftwareC,3.0+
SoftwareB,2.2,SoftwareC,3.2+
SoftwareC,3.2,,
SoftwareC,3.5,,
                """, language="csv")
        
        with col2:
            # Upload current versions file
            current_versions_file = st.file_uploader("Upload current software versions", type="json")
            
            # Display example format
            with st.expander("Example current versions format"):
                st.code("""
{
  "SoftwareA": "1.0",
  "SoftwareB": "2.1",
  "SoftwareC": "3.2"
}
                """, language="json")
    else:
        st.info("Using sample data: SoftwareA, SoftwareB, SoftwareC dependencies")
    
    # Software selection and version input
    col3, col4, col5 = st.columns(3)
    
    with col3:
        software_to_upgrade = st.text_input("Software to upgrade", 
                                          value="SoftwareA" if use_sample_data else "",
                                          placeholder="e.g., SoftwareA")
    
    with col4:
        target_version = st.text_input("Target version", 
                                     value="2.0" if use_sample_data else "",
                                     placeholder="e.g., 2.0")
    
    with col5:
        criteria = st.selectbox(
            "Criteria for selecting dependent upgrades",
            options=["minimum_changes", "latest_available"],
            format_func=lambda x: "Minimum Changes" if x == "minimum_changes" else "Latest Available"
        )
    
    # Check if we can run the analysis
    can_analyze = (use_sample_data or (master_sheet_file and current_versions_file)) and software_to_upgrade and target_version
    
    if can_analyze:
        if st.button("Analyze Dependencies", type="primary"):
            with st.spinner("Analyzing software dependencies..."):
                try:
                    # Create a temporary directory to save the uploaded files
                    with tempfile.TemporaryDirectory() as temp_dir:
                        if use_sample_data:
                            # Use sample data
                            master_sheet_path = "sample_data/software_dependencies.csv"
                            current_versions_path = "sample_data/current_versions.json"
                        else:
                            # Save master sheet to temporary file
                            master_sheet_path = os.path.join(temp_dir, "dependencies.csv")
                            with open(master_sheet_path, "wb") as f:
                                f.write(master_sheet_file.getbuffer())
                            
                            # Save current versions to temporary file
                            current_versions_path = os.path.join(temp_dir, "current_versions.json")
                            with open(current_versions_path, "wb") as f:
                                f.write(current_versions_file.getbuffer())
                        
                        # Create a StringIO to capture print output
                        import io
                        import sys
                        old_stdout = sys.stdout
                        new_stdout = io.StringIO()
                        sys.stdout = new_stdout
                        
                        try:
                            # Run the dependency analysis
                            dependency_analysis.run(
                                master_sheet_path, 
                                current_versions_path, 
                                software_to_upgrade, 
                                target_version, 
                                criteria
                            )
                            
                            # Get the output
                            output = new_stdout.getvalue()
                            
                            # Restore stdout
                            sys.stdout = old_stdout
                            
                            # Display the analysis results
                            st.code(output, language="plain")
                            
                            # Try to extract the JSON results
                            try:
                                import re
                                json_str = re.search(r'(\{.*\})', output, re.DOTALL)
                                if json_str:
                                    upgrades = json.loads(json_str.group(1))
                                    
                                    # Display as a table
                                    if upgrades:
                                        data = []
                                        for software, details in upgrades.items():
                                            data.append({
                                                "Software": software,
                                                "Current Version": details["current_version"],
                                                "Required Version": details["required_version"],
                                                "Required By": details["required_by"]
                                            })
                                        
                                        st.subheader("Upgrade Summary")
                                        st.table(pd.DataFrame(data))
                            except Exception as e:
                                st.warning(f"Could not parse detailed results: {str(e)}")
                            
                        finally:
                            # Restore stdout
                            sys.stdout = old_stdout
                except Exception as e:
                    st.error(f"Error analyzing dependencies: {str(e)}")
    else:
        if not use_sample_data:
            st.warning("Please upload both the dependency sheet and current versions file, and specify the software to upgrade and target version.")

# Software Change Notice Aggregation
elif page == "Software Change Notice Aggregation":
    st.header("Software Change Notice Aggregation")
    st.markdown("""
    This feature aggregates software change notices between versions.
    
    Upload your Software Change Notice (SCN) PDFs and specify the version range.
    """)
    
    # File uploader for SCN PDFs
    uploaded_files = st.file_uploader("Upload SCN PDFs", type="pdf", accept_multiple_files=True)
    
    # Software and version input
    col1, col2, col3 = st.columns(3)
    
    with col1:
        software_name = st.text_input("Software name", placeholder="e.g., SoftwareX")
    
    with col2:
        current_version = st.text_input("Current version", placeholder="e.g., 1.0")
    
    with col3:
        target_version = st.text_input("Target version", placeholder="e.g., 1.5")
    
    # Output format selection
    output_format = st.radio("Output format", ["Markdown", "CSV"], horizontal=True)
    
    if uploaded_files and software_name and current_version and target_version:
        if st.button("Aggregate Change Notices", type="primary"):
            with st.spinner("Aggregating software change notices..."):
                # Create a temporary directory to save the uploaded files
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files to the temporary directory
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    
                    # Create a temporary output file
                    output_file = os.path.join(
                        temp_dir, 
                        f"aggregated_scn.{'md' if output_format == 'Markdown' else 'csv'}"
                    )
                    
                    # Run the SCN aggregation
                    scn_aggregation.run(
                        temp_dir, 
                        software_name, 
                        current_version, 
                        target_version, 
                        output_file
                    )
                    
                    # Display the results
                    if os.path.exists(output_file):
                        st.success(f"Successfully aggregated change notices.")
                        
                        if output_format == "Markdown":
                            with open(output_file, "r") as f:
                                md_content = f.read()
                            st.markdown(md_content)
                        else:  # CSV
                            df = pd.read_csv(output_file)
                            st.dataframe(df)
                        
                        # Download button for the output file
                        with open(output_file, "rb") as file:
                            file_extension = "md" if output_format == "Markdown" else "csv"
                            mime_type = "text/markdown" if output_format == "Markdown" else "text/csv"
                            st.download_button(
                                label=f"Download {output_format}",
                                data=file,
                                file_name=f"aggregated_scn.{file_extension}",
                                mime=mime_type,
                            )
                    else:
                        st.error("Failed to aggregate change notices.")

# Add footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Document Crawler and Analyzer v1.0.0\n\n"
    "Powered by Llama 3.3 via Groq"
) 