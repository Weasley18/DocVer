# Document Crawler and Analyzer

A Python application that uses CrewAI with Llama 3.3 (via Groq) to orchestrate document analysis tasks. It provides functionality for critical information extraction from PDFs, software dependency analysis, and software change notice aggregation.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory with your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

You can obtain a Groq API key by signing up at [https://console.groq.com/](https://console.groq.com/).

## Demo Data Generation

For demonstration purposes, you can generate sample PDF files:

```bash
python create_sample_pdfs.py
```

This will create:
- A sample invoice PDF in the `sample_pdfs` directory
- Sample Software Change Notice PDFs in the `sample_scns` directory

These sample files can be used to test the application features without needing to upload your own documents.

## Usage

### Web Interface

The application provides a user-friendly web interface built with Streamlit:

```bash
streamlit run app.py
```

This will start a local web server and open the application in your browser. From there, you can:
- Upload PDF documents for information extraction
- Upload dependency data for software analysis
- Upload SCN PDFs for change notice aggregation

### Command Line Interface

Alternatively, you can use the command line interface:

#### 1. Critical Information Extraction

Extract predefined fields from PDF documents:

```bash
python main.py extract --folder /path/to/pdfs --fields "Invoice Number" "Date" "Total Amount" --output extracted_data.csv
```

#### 2. Software Dependency Analysis

Analyze software dependencies for an upgrade:

```bash
python main.py analyze-deps --master-sheet dependencies.csv --current current_versions.json --software "SoftwareA" --target-version "2.0" --criteria minimum_changes
```

#### 3. Software Change Notice Aggregation

Aggregate change notices between software versions:

```bash
python main.py aggregate-scn --folder /path/to/scn_pdfs --software "SoftwareX" --current-version "1.0" --target-version "1.5" --output changes.md
```

## Example Input Formats

### Current Software Versions (JSON)

```json
{
  "SoftwareA": "1.0",
  "SoftwareB": "2.1",
  "SoftwareC": "3.2"
}
```

### Master Dependency Sheet (CSV)

```csv
SoftwareName,Version,DependsOnSoftware,DependsOnVersion
SoftwareA,2.0,SoftwareB,2.1+
SoftwareA,2.0,SoftwareC,3.5+
SoftwareB,2.1,SoftwareC,3.0+
``` 