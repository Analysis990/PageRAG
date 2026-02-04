from qdrant_client import QdrantClient
import os

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL)
print(f"Type of client: {type(client)}")
print(f"All attributes with 'search': {[attr for attr in dir(client) if 'search' in attr.lower()]}")

# Try to see if we can use 'query' as a search replacement
try:
    print("Testing 'query' method signature...")
    import inspect
    print(f"Query signature: {inspect.signature(client.query)}")
except Exception as e:
    print(f"Error checking query: {e}")
