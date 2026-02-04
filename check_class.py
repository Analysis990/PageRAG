from qdrant_client import QdrantClient
print(f"Attributes of QdrantClient class: {[attr for attr in dir(QdrantClient) if 'search' in attr.lower()]}")
