from qdrant_client import QdrantClient
import os

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL)
print(f"Type of client: {type(client)}")
print(f"Has search attribute: {hasattr(client, 'search')}")
print(f"Available attributes: {[attr for attr in dir(client) if not attr.startswith('_')]}")
