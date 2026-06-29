import os
import sys

# Add parent directory to path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient


def check_indexed():
    # Use direct URL instead of environment variable if not set properly in this script context
    client = QdrantClient(url="http://qdrant:6333")
    collection_name = "uphill_athlete_materials"

    # We will scroll through the points and collect the 'source' payload
    sources = set()
    offset = None

    while True:
        records, next_offset = client.scroll(
            collection_name=collection_name, limit=100, offset=offset, with_payload=True, with_vectors=False
        )

        for record in records:
            if record.payload and "metadata" in record.payload and "source" in record.payload["metadata"]:
                sources.add(record.payload["metadata"]["source"])

        if next_offset is None:
            break
        offset = next_offset

    print("INDEXED SOURCES:")
    for source in sorted(sources):
        print(f"- {source}")


if __name__ == "__main__":
    check_indexed()
