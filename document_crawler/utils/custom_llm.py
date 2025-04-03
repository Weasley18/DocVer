"""
Custom LLM implementation for Groq.
"""
import os
from dotenv import load_dotenv
from crewai import Agent
from langchain_openai import ChatOpenAI

# Print debug info
print(">>> Loading custom_llm.py - new implementation <<<")

# Disable proxies in the environment
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["NO_PROXY"] = "*"

# Load environment variables
load_dotenv()

# Get API key from environment and set it for CrewAI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in the .env file.")

def create_document_agent(verbose=True, allow_delegation=False):
    """
    Create a document analyzer agent using Llama 3.3 via Groq.
    
    Args:
        verbose (bool, optional): Whether to enable verbose output. Defaults to True.
        allow_delegation (bool, optional): Whether to allow delegation. Defaults to False.
        
    Returns:
        Agent: A document analyzer agent configured with Llama 3.3.
    """
    print(">>> Creating document agent with ChatOpenAI <<<")
    
    # Use ChatOpenAI with Groq's API (they have OpenAI API compatibility)
    llm = ChatOpenAI(
        model="llama3-70b-8192", 
        temperature=0.2,
        openai_api_key=GROQ_API_KEY,
        openai_api_base="https://api.groq.com/openai/v1"
    )
    
    # Create the document analyzer agent
    return Agent(
        role="Document Analyzer",
        goal="Extract detailed, comprehensive information from documents with a focus on providing all relevant details for each requested field.",
        backstory="You are an expert analyst specializing in detailed document extraction. You excel at identifying all relevant information for requested fields, especially when dealing with technical documents. You provide thorough, comprehensive answers rather than brief summaries, and you make sure to include all details that could be important for each requested field.",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=llm
    ) 