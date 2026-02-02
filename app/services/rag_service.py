import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient

# Load env variables (normally handled by main's load_dotenv, but good to be safe)
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def query(message: str):
    """
    Query the RAG knowledge base.
    """
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not found.", []

    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        client = QdrantClient(url=QDRANT_URL)
        
        # Check if collection exists (basic check, in prod we might handle differently)
        # For now, we assume the collection 'rag_documents' is created by process_rag.py
        
        vector_store = Qdrant(
            client=client, 
            collection_name="rag_documents", 
            embeddings=embeddings,
        )
        
        # Create a retriever
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Initialize LLM
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo")
        
        # Create QA Chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever,
            return_source_documents=True
        )
        
        # Run query
        result = qa_chain.invoke({"query": message})
        
        answer = result["result"]
        source_docs = result["source_documents"]
        
        # Format sources
        sources_list = [doc.metadata.get("source", "Unknown") for doc in source_docs]
        
        return answer, list(set(sources_list))

    except Exception as e:
        print(f"RAG Error: {e}")
        return f"Error processing request: {str(e)}", []
