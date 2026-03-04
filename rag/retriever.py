# rag/retriever.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

VECTORSTORE_DIR = "vectorstore"

print("Loading embedding model...")

# Load embedding model ONCE
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Loading vector store...")

# Load Chroma ONCE
vectordb = Chroma(
    persist_directory=VECTORSTORE_DIR,
    embedding_function=embeddings
)

# Create retriever ONCE
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

print("Retriever ready.")


# ============================================
# Retrieve Context
# ============================================

def retrieve_context(question: str) -> str:
    docs = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in docs)


# ============================================
# Test
# ============================================

if __name__ == "__main__":
    query = "How are customers and orders related in the database?"
    print(f"\nQuery: {query}\n")

    results = retrieve_context(query)

    print("Retrieved context:\n")
    print(results)
