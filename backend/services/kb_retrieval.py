"""Qdrant semantic retrieval for scheduler-domain philosophy chunks.

Sync functions (embedding + Qdrant calls are blocking) — async callers must wrap
in asyncio.to_thread. Uses plain qdrant-client + genai.embed_content; see
services/vector_service.py note in the implementation plan for why langchain
is intentionally avoided here.
"""

import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import settings

COLLECTION = "uphill_kb_scheduler"
EMBEDDING_MODEL = "models/gemini-embedding-2"
VECTOR_SIZE = 3072


def _client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def _embed(texts: list[str], api_key: str, task_type: str) -> list[list[float]]:
    genai.configure(api_key=api_key)
    vectors = []
    for t in texts:
        result = genai.embed_content(model=EMBEDDING_MODEL, content=t, task_type=task_type)
        vectors.append(result["embedding"])
    return vectors


def reindex_scheduler_chunks(chunks: list[dict], api_key: str) -> int:
    """Drop and rebuild the scheduler philosophy collection from kb_chunks rows."""
    client = _client()
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    texts = [f"{c.get('title', '')}\n{c.get('content', '')}" for c in chunks]
    vectors = _embed(texts, api_key, task_type="retrieval_document")
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload={"title": chunk.get("title", ""), "content": chunk.get("content", "")},
        )
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"[KBRetrieval] Reindexed {len(points)} scheduler chunks into {COLLECTION}")
    return len(points)


def scheduler_point_count() -> int | None:
    """Point count of the scheduler philosophy collection, or None if unreachable/missing."""
    try:
        client = _client()
        if not client.collection_exists(COLLECTION):
            return None
        return client.count(collection_name=COLLECTION).count
    except Exception as e:
        print(f"[KBRetrieval] Could not read collection count: {e}")
        return None


def search_scheduler_chunks(query: str, api_key: str, k: int = 6) -> list[dict]:
    """Top-k philosophy chunks for a retrieval query. [] if collection absent."""
    client = _client()
    if not client.collection_exists(COLLECTION):
        print(f"[KBRetrieval] Collection {COLLECTION} does not exist — returning no context")
        return []
    vector = _embed([query], api_key, task_type="retrieval_query")[0]
    hits = client.query_points(collection_name=COLLECTION, query=vector, limit=k).points
    return [{"title": h.payload.get("title", ""), "content": h.payload.get("content", "")} for h in hits if h.payload]
