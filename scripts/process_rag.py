import os
import glob
from langchain_community.document_loaders import TextLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATA_DIR = "data/rag_source"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

def process_rag():
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in .env")
        return

    print("Starting RAG processing...")
    
    # 1. Load Documents
    documents = []
    # simple glob for txt files, can be expanded
    file_paths = glob.glob(os.path.join(DATA_DIR, "*"))
    
    if not file_paths:
        print(f"No files found in {DATA_DIR}")
        return

    for file_path in file_paths:
        try:
            # Using Unstructured for versatility if available, else TextLoader
            if file_path.endswith(".txt"):
                loader = TextLoader(file_path)
            else:
                # Fallback or specific loaders can be added here
                print(f"Skipping unsupported file type: {file_path}")
                continue
                
            docs = loader.load()
            # Add metadata if needed
            for doc in docs:
                doc.metadata["source"] = os.path.basename(file_path)
            documents.extend(docs)
            print(f"Loaded {len(docs)} documents from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if not documents:
        print("No valid documents to process.")
        return

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks.")

    # 3. Embed and Store in Qdrant
    embeddings_kwargs = {"openai_api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        embeddings_kwargs["openai_api_base"] = OPENAI_BASE_URL
    embeddings = OpenAIEmbeddings(**embeddings_kwargs)
    
    try:
        from qdrant_client.http import models
        # 1. Initialize the native Qdrant client
        client = QdrantClient(url=QDRANT_URL)
        
        # 2. Manually recreate the collection (equivalent to force_recreate=True)
        # Using 1536 as the size because OpenAI text-embedding-3-small outputs 1536 dimensions
        client.recreate_collection(
            collection_name="rag_documents",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
        
        # 3. Initialize the LangChain Qdrant wrapper with the existing client
        qdrant = Qdrant(
            client=client,
            collection_name="rag_documents",
            embeddings=embeddings
        )
        
        # 4. Add the documents
        qdrant.add_documents(texts)
        
        print(f"Successfully indexed {len(texts)} chunks to Qdrant collection 'rag_documents'.")
    except Exception as e:
        print(f"Error connecting to Qdrant or indexing: {e}")

if __name__ == "__main__":
    process_rag()
