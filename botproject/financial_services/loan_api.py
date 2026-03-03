from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.document_loaders import PyPDFLoader
from ai_chat_components.vectore_store import prepare_vectorstore
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_community.tools import DuckDuckGoSearchRun
import requests
import warnings
import logging
from langchain.agents import Tool, create_react_agent, AgentExecutor
import json


logging.captureWarnings(True)

# Load environment variables
load_dotenv()


def get_loan_details(input_text: str, access_token: str, user_id: int) -> str:
    url = "https://api.prod.eazr.in/instacash/all-loan"
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        response_data = response.json()

        print(response_data)  # For debug; remove in production

        return response_data  # Or json.dumps(response_data) if needed
    except Exception as e:
        return f"Error fetching loan details: {str(e)}"
    

