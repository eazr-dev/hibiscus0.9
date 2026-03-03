# Fixed vectore_store.py - Updated imports to resolve deprecation warnings

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os
print('a')
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def prepare_vectorstore(pdf_paths=None):
    """
    Prepare vector store from PDF documents
    If no pdf_paths provided, create empty vectorstore or load existing one
    """
    if pdf_paths is None:
        pdf_paths = []
    
    # If no PDFs provided, try to load existing index or create empty one
    if not pdf_paths:
        try:
            # Try to load existing FAISS index
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            return vectorstore
        except:
            # Create empty vectorstore with dummy document
            from langchain.schema import Document
            dummy_docs = [Document(page_content="Welcome to Eazr Financial Assistant", metadata={"source": "system"})]
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vectorstore = FAISS.from_documents(dummy_docs, embeddings)
            return vectorstore
    
    # Load documents from PDFs
    all_docs = []
    for path in pdf_paths:
        if os.path.exists(path):
            loader = PyPDFLoader(path)
            all_docs.extend(loader.load())
        else:
            print(f"Warning: PDF file not found: {path}")

    if not all_docs:
        # Create dummy document if no PDFs loaded
        from langchain.schema import Document
        all_docs = [Document(page_content="Welcome to Eazr Financial Assistant", metadata={"source": "system"})]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(all_docs)

    # Create embeddings and vectorstore
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = FAISS.from_documents(docs, embeddings)

    return vectorstore