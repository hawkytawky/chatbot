# Basics
import os
import sys
import json
import hashlib
import warnings
from typing import List

# Warnings
import logging
import langchain
langchain.debug = False
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# Environmen variables
from dotenv import load_dotenv

# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# Server
import uvicorn

# OpenAI and LangChain
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain_core._api.deprecation import LangChainDeprecationWarning

# Import predefined functions
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from database.functions import (
    get_embeddings, 
    match_documents,
    llm_best_retrieved_sections
)

# Get OpenAI key
env_path = os.path.join(os.path.dirname(__file__), '..', 'secrets', '.env')
load_dotenv(dotenv_path=env_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define strong llm model (gpt-4-turbo)
llm_gpt4turbo = ChatOpenAI(openai_api_key=OPENAI_API_KEY, 
                           model='gpt-4-0125-preview', 
                           temperature=0.1)

# Define weaker llm model (gpt-3.5)
llm_gpt3 = ChatOpenAI(openai_api_key=OPENAI_API_KEY, 
                      model='gpt-3.5-turbo-1106', 
                      temperature=0.1)

# FastAPI-App-Instance
app = FastAPI()

# CORS-Middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Class for chat history
class ChatMessage(BaseModel):
    sender: str = Field(description="Sender of the message ('user' or 'bot')")
    text: str = Field(description="Text of the message")

# Set request body
class InputRequest(BaseModel):
    user_input: str = Field(description="Question or prompt from the user")
    chat_history: List[ChatMessage] = Field(description="Chat history from previous prompts")

# Ask endpoint
@app.post("/ask")
async def ask(request_body: InputRequest):

    # Retrieve best sections based on similarity score
    embedding_question = get_embeddings(request_body.user_input)
    match_response = await match_documents(embedding_question, 0.6, 4)
    contents = [item['content'] for item in match_response.data]

    # LLM response
    llm_response = llm_best_retrieved_sections(strong_llm=llm_gpt4turbo,
                                               weak_llm=llm_gpt3,
                                               retrieved_sections=contents,
                                               chat_history=request_body.chat_history,
                                               user_input=request_body.user_input)

    return llm_response

# Password request body
class PasswordRequest(BaseModel):
    password: str = Field(description="Password string from user on login page")

# Check login password endpoint 
@app.post("/login")
async def login(request_body: PasswordRequest):
    # Load hashed password
    with open('../secrets/login_key.json', 'r') as json_file:
        stored_data = json.load(json_file)

    stored_hashed_password = stored_data['hashed_password']

    # Hash input password
    hashed_input_password = hashlib.sha256(request_body.password.encode()).hexdigest()

    # Compare hashed passwords
    if hashed_input_password == stored_hashed_password:
        return {"message": "Successful Authentication"}
    else:
        raise HTTPException(status_code=401, detail="Wrong Password")

# Redirect endpoint to swagger UI
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)