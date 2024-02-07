import PyPDF2
import openai
import json
from supabase import create_client, Client
import langchain
langchain.debug = False
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from typing import List, Tuple
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

# Set up supabase client
path_to_sup_key = "../secrets/supabase_key.json"
with open(path_to_sup_key, 'r') as file:
    config = json.load(file)
supabase_url = config["project_url"]
supabase_service_key = config["service_role_key"]
supabase: Client = create_client(supabase_url, supabase_service_key)

# Text chunking
def extract_and_chunk_pdf(path, chunk_size, chunk_overlap):
    """
    Extracts text from a PDF file, removes newline characters, and splits the text into chunks.

    Args:
    - path (str): File path of the PDF.
    - chunk_size (int): Number of characters in each chunk.
    - chunk_overlap (int): Number of characters that overlap between consecutive chunks.

    Returns:
    - list: A list of text chunks.
    """

    # Open and extract text from pdf
    with open(path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = "".join(page.extract_text() for page in reader.pages)

    # Remove newline characters
    full_text = full_text.replace('\n', ' ')

    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    # Split text into chunks
    text_chunks = text_splitter.split_text(full_text)

    return text_chunks


# Transforms text in embeddings using openai
def get_embeddings(text, model="text-embedding-ada-002"):
    """Transforms text in embeddings"""
    return openai.embeddings.create(input = [text], model=model).data[0].embedding

# Upload to supbase
def upload_to_database(path, chunk_size, chunk_overlap, supabase: Client):
    """
    Extracts text chunks from a PDF, computes their embeddings, and uploads to the Supabase database.

    Args:
    - path (str): File path of the PDF.
    - chunk_size (int): Number of characters in each chunk.
    - chunk_overlap (int): Number of characters that overlap between consecutive chunks.
    - supabase (Client): Supabase client object for database operations.
    """

    # Extract text chunks from PDF
    text_chunks = extract_and_chunk_pdf(path, chunk_size, chunk_overlap)

    # Iterate over each chunk, compute embeddings, and upload to database
    for i, chunk in enumerate(text_chunks):
        embeddings = get_embeddings(chunk)
        
        # Prepare the data to be inserted
        data = {
            "content": chunk,
            "embeddings": embeddings
        }

        # Insert data into the database
        supabase.table('documents2').insert(data).execute()

        print(f'Successfully uploaded chunk {i}')


# Fetches best matched section
async def match_documents(query_embedding, match_threshold, match_count):
    """
    Matches documents based on the provided query embedding.

    This function communicates with a database using the Supabase client to find documents 
    that match a given query embedding. It calls SQL match_documents function defined in supabase. 
    The matching is based on a specified threshold and a maximum count of documents to match.

    Args:
    - query_embedding: The embedding vector representing the query. Expecting a 1536 dimensional list/array
    - match_threshold (float): The threshold value for matching documents based on cosine similarity
    - match_count (int): The maximum number of documents to return that match the query.

    Returns:
    - response: The response from the database or service containing the matched documents. 
                The exact format of this response depends on the implementation of the 'match_documents' 
                RPC function.
    """

    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count
        }
    ).execute()

    return response

# Class for chat history
class ChatMessage(BaseModel):
    sender: str = Field(description="Sender of the message ('user' or 'bot')")
    text: str = Field(description="Text of the message")

# Summary prompt
def summarize_old_chat_history(
    weak_llm, 
    chat_history: List[ChatMessage],
) -> Tuple[str, str]:
    """
    Generates a summary of older chat messages and keeps track of the last two messages.

    This function takes a list of ChatMessage objects and a weak language model (LLM).
    It returns a string containing the last two messages and a summary of older messages if the history is longer than six messages.
    
    Args:
    - weak_llm: A language model used for generating summaries of older chat messages.
    - chat_history: A list of ChatMessage objects representing the entire chat history.

    Returns:
    - A tuple containing two strings: the concatenated last two messages and a summary of older messages.
    """
    
    # Last two messages
    previous_messages = chat_history[-3:-1] if len(chat_history) >= 3 else chat_history[:-1]
    previous_messages_str = ' '.join([f"{msg.sender}: {msg.text}" for msg in previous_messages])

    # Initialize
    old_messages_summary_str = ""

    if len(chat_history) > 6:
        old_messages_for_summary = chat_history[:-2]
        old_messages_str = ' '.join([f"{msg.sender}: {msg.text}" for msg in old_messages_for_summary])

        # Summarize prompt
        prompt_template = PromptTemplate.from_template(
            """
            Write a concise summary of the following:
            "{text}"
            CONCISE SUMMARY:
            """
        )

        # Create chain 
        chain = LLMChain(llm=weak_llm, prompt=prompt_template)

        # Run chain
        response = chain({"text": list(old_messages_str)})

        old_messages_summary_str = response['text']

    return previous_messages_str, old_messages_summary_str


# Langchain prompt
def llm_best_retrieved_sections(
    strong_llm, 
    weak_llm, 
    retrieved_sections: [], 
    chat_history: List[ChatMessage],
    user_input: str
) -> str:
    """
    Generates a response from a language model using retrieved sections, chat history, and user input.

    This function constructs a prompt for a strong language model (LLM) to generate a response. It incorporates the latest two messages from the chat history and a summary of older messages if the history is extensive. It utilizes a weaker LLM for summarizing older messages.

    Args:
    - strong_llm: The primary language model used for generating the final response.
    - weak_llm: A secondary, weaker language model used for summarizing older chat messages.
    - retrieved_sections: A list of strings representing relevant information sections.
    - chat_history: A list of ChatMessage objects representing the chat history.
    - user_input: The latest user input as a string.

    Returns:
    - The generated response from the strong language model as a string.
    """
    
    # Convert to string
    retrieved_sections_str = ' '.join(retrieved_sections)

    # Preprocess chat history
    if len(chat_history) > 1: 
        previous_messages_str, old_messages_summary_str = summarize_old_chat_history(weak_llm=weak_llm, chat_history=chat_history)
    else: 
        previous_messages_str = ""
        old_messages_summary_str = ""

    # Prompt template
    prompt_template = PromptTemplate.from_template(
        """
        You are a personal chatbot representing Philipp Habicht. 
        Your purpose is to give short, concise and accurate answer about the question of Philipps career, education, skills, and experiences in a professional and engaging manner. 
        Use the first-person perspective and maintain a professional but friendly and easy-going tone. Responses should be short, concise, informative, and directly relevant to the questions asked. 
        -------
        The user has the question: {user_input}. 
        -------
        ONLY use the following information to answer this question: {retrieved_sections_str} OR
        the context information provided: Here are two previous messages {previous_messages_str} and a summary of the older messages before {old_messages_summary_str}. If this is empty, just use the previous messages as context.
        -------
        If this question cannot be answered by the given informatinon, say that you do not provide about the relevant information to answer this question. 
        IMPORTANT: ALWAYS reply in ENGLISH! 
        """
    )

    # Create chain 
    chain = LLMChain(llm=strong_llm, prompt=prompt_template)

    # Run chain
    response = chain({"user_input": user_input, 
                      "retrieved_sections_str": retrieved_sections_str, 
                      "previous_messages_str": previous_messages_str,
                      "old_messages_summary_str": old_messages_summary_str})

    # Extract
    llm_response = response['text']

    return llm_response