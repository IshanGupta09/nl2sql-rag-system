import os
import sqlite3

from dotenv import load_dotenv

#from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
#from langchain_openai import OpenAIEmbeddings
#from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import Chroma
#from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
load_dotenv()

# -----------------------------
# PATH SETUP
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "data", "ecommerce.db")
RULES_PATH = os.path.join(BASE_DIR, "docs", "business_rules.txt")
VECTORSTORE_PATH = os.path.join(BASE_DIR, "vectorstore")

# -----------------------------
# LOAD BUSINESS RULES
# -----------------------------
print("Loading business rules...")

rules_loader = TextLoader(RULES_PATH)
rules_docs = rules_loader.load()

# -----------------------------
# LOAD DATABASE SCHEMA
# -----------------------------
print("Loading database schema...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

schema_texts = []

for (table_name,) in tables:
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    schema_description = f"Table: {table_name}\nColumns: {', '.join(column_names)}"
    schema_texts.append(
        Document(page_content=schema_description, metadata={"source": "schema"})
    )

conn.close()

# -----------------------------
# COMBINE ALL DOCUMENTS
# -----------------------------
all_docs = rules_docs + schema_texts

# -----------------------------
# SPLIT TEXT INTO CHUNKS
# -----------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

split_docs = text_splitter.split_documents(all_docs)

#if not os.getenv("OPENAI_API_KEY"):
#    raise ValueError("OPENAI_API_KEY not found. Check your .env file.")
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# -----------------------------
# CREATE EMBEDDINGS & STORE
# -----------------------------
print("Creating embeddings and storing in vector DB...")

#embeddings = OpenAIEmbeddings()
#embeddings = GoogleGenerativeAIEmbeddings(
#    model="models/text-embedding-004"
#)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=split_docs,
    embedding=embeddings,
    persist_directory=VECTORSTORE_PATH
)

vectorstore.persist()

print("RAG ingestion completed successfully!")
