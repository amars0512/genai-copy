# pip install llama-index chromadb llama-index-vector-stores-chroma openai

# VectoreStoreIndex = RAG Orchestration 
# ChromaVectorStore = Storage backend
# chromadb = Actual database engine
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(override=True)

# -------------------------------
# Configure LLM
# -------------------------------
Settings.llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# -------------------------------
# Create / connect ChromaDB (PERSISTENT)
# -------------------------------
chroma_client = chromadb.PersistentClient(
    path=os.path.join(BASE_DIR, "chromadb")
)

collection = chroma_client.get_or_create_collection(
    name="darwin_books"
)

# Bridge between ChromaDB and LlamaIndex
# Without this, LlamaIndex would not know how to insert vectors
# Chroma would not know about chunk metadata
vector_store = ChromaVectorStore(
    chroma_collection=collection
)

# -------------------------------
# Load documents
# -------------------------------
documents = SimpleDirectoryReader(
    input_files=[
        os.path.join(BASE_DIR, "..", "..", "3_langgraph", "darwin", "Origin-of-Species.txt")
    ]
).load_data()

# -------------------------------
# Build index USING ChromaDB
# -------------------------------
# Chunking (~512 token chunks, Add overlap)
# Embeddings: Each chunk -> Vector embedding
# Insertion: Vectors stored in ChromaDB, Metadata preserved
# Persistence: Chroma saves it to the disk
index = VectorStoreIndex.from_documents(
    documents,
    vector_store=vector_store
)

# -------------------------------
# Query
# -------------------------------
query_engine = index.as_query_engine()
response = query_engine.query(
    "What is natural selection?"
)

print(response)
