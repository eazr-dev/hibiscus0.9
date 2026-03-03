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


def get_usr_wallet_data(input_text: str, access_token: str, user_id: int) -> str:
    url = f"https://api.prod.eazr.in/flex-ac/{user_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.request("GET", url, headers=headers)
    data = response.json()
    data_output ={'balance':data['data']['balance'],
            'outstanding':data['data']['outstanding'],
            'setLimit':data['data']['setLimit'],
            'unbilled':data['data']['unbilled'],
            'lastBill':data['data']['lastBill'],
            'nextBillDate':data['data']['nextBillDate']}

    return data_output


# def get_user_statement(data: str) -> str:
#     url = "https://api.prod.eazr.in/flex-ac/282"
#     access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjgyLCJjb250YWN0TnVtYmVyIjoiNzAyMTk0ODgwNiIsIm5hbWUiOiJIcnVzaGlrZXNoIFJhamVzaCBUZW1iZSIsImlwIjoiMTA2LjIyMi4yMDUuMTUzIiwidXNlckFnZW50IjoiUG9zdG1hblJ1bnRpbWUvNy40NC4xIiwicm9sZSI6InVzZXIiLCJ0aW1lc3RhbXAiOiIxNzUwNzU1Mzk5MzQxIiwiaWF0IjoxNzUwNzU1Mzk5LCJleHAiOjE3NTEzNjAxOTl9.oI_b61Zfi4NIQ06Rgzl9pqDh-LQ6_OsDqxh7bg6xbzs"
#     try:
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         response = requests.request("GET", url, headers=headers)
#         data = response.json()

#         activities = data.get("data", {}).get("activities", [])
#         if not activities:
#             return "No recent transaction activities found."
#         return activities
#     except Exception as e:
#         return f"Error fetching user statement: {str(e)}"
    

