"""
Configuration for Llama 3.3 model with Groq.
"""
import os
import sys
from dotenv import load_dotenv
from crewai import Agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Debug print to verify this file is being used
print(">>> Loading updated llm_config.py with ChatOpenAI <<<")
print(f">>> Python version: {sys.version} <<<")
print(f">>> File path: {__file__} <<<")

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

# Set the API key in the environment
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

def create_agent(role, goal, backstory, verbose=True, allow_delegation=False):
    """
    Create an agent with Llama 3.3 model.
    
    Args:
        role (str): The role of the agent.
        goal (str): The goal of the agent.
        backstory (str): The backstory of the agent.
        verbose (bool, optional): Whether to enable verbose output. Defaults to True.
        allow_delegation (bool, optional): Whether to allow delegation. Defaults to False.
        
    Returns:
        Agent: A CrewAI agent configured with Llama 3.3.
    """
    # Debug print to verify this function is being called
    print(">>> Creating agent with ChatOpenAI + Groq API <<<")
    
    # Create Chat model using ChatOpenAI pointing to Groq's API
    # Groq provides OpenAI API compatibility
    llm = ChatOpenAI(
        model="groq/llama3-70b-8192",
        temperature=0.2,
        openai_api_key=GROQ_API_KEY,
        openai_api_base="https://api.groq.com/openai/v1",
        http_client_extra_kwargs={"trust_env": False}  # Disable proxy lookup from environment
    )
    
    # Create and return the agent with the LLM
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=llm
    ) 