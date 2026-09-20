"""Qdrant semantic retrieval for scheduler-domain philosophy chunks.

Sync functions (embedding + Qdrant calls are blocking) — async callers must wrap
in asyncio.to_thread. Uses plain qdrant-client + genai Client.models.embed_content;
see services/vector_service.py note in the implementation plan for why langchain
is intentionally avoided here.
"""

import hashlib

from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import settings
from services import observability

COLLECTION_SCHEDULER = "uphill_kb_scheduler"
COLLECTION_NUTRITION_PRINCIPLES = "uphill_kb_nutrition_principles"
COLLECTION = COLLECTION_SCHEDULER
EMBEDDING_MODEL = "models/gemini-embedding-2"
VECTOR_SIZE = 3072


def _client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def _embed(texts: list[str], api_key: str, task_type: str) -> list[list[float]]:
    client = genai.Client(api_key=api_key)
    vectors = []
    for t in texts:
        with observability.generation(
            "generation",
            feature="embeddings",
            model=EMBEDDING_MODEL,
            metadata={"collections": [COLLECTION]},
        ) as generation:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL, contents=t, config=types.EmbedContentConfig(task_type=task_type)
            )
            usage_metadata = getattr(result, "usage_metadata", None)
            if usage_metadata is not None:
                generation.set_usage(observability.Usage.from_genai(usage_metadata))
        vectors.append(result.embeddings[0].values)
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


def _chunk_ref(title: str, content: str) -> str:
    """Stable 12-hex id for a chunk. Qdrant point ids are enumerate() indexes that
    change on every reindex; this doesn't, so traces can name the chunks they used."""
    return hashlib.sha1(f"{title}\n{content}".encode()).hexdigest()[:12]


def search_scheduler_chunks(query: str, api_key: str, k: int = 6) -> list[dict]:
    """Top-k philosophy chunks for a retrieval query: title, content, score, ref. [] if collection absent."""
    with observability.span(
        "retrieval",
        metadata={"collections": [COLLECTION], "retrieval_k": k},
    ) as retrieval:
        client = _client()
        if not client.collection_exists(COLLECTION):
            retrieval.set(grounded=False, chunk_refs=[], chunk_scores=[])
            print(f"[KBRetrieval] Collection {COLLECTION} does not exist — returning no context")
            return []
        vector = _embed([query], api_key, task_type="retrieval_query")[0]
        hits = client.query_points(collection_name=COLLECTION, query=vector, limit=k).points
        results = []
        for hit in hits:
            if not hit.payload:
                continue
            title = hit.payload.get("title", "")
            content = hit.payload.get("content", "")
            results.append(
                {"title": title, "content": content, "score": float(hit.score), "ref": _chunk_ref(title, content)}
            )
        retrieval.set(
            grounded=bool(results),
            chunk_refs=[result["ref"] for result in results],
            chunk_scores=[result["score"] for result in results],
        )
        return results


def reindex_nutrition_principles(chunks: list[dict], api_key: str) -> int:
    """Drop and rebuild the nutrition principles collection from kb_chunks rows."""
    client = _client()
    if client.collection_exists(COLLECTION_NUTRITION_PRINCIPLES):
        client.delete_collection(COLLECTION_NUTRITION_PRINCIPLES)
    client.create_collection(
        collection_name=COLLECTION_NUTRITION_PRINCIPLES,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    texts = [f"{c.get('title', '')}\n{c.get('content', '')}" for c in chunks]
    vectors = _embed(texts, api_key, task_type="retrieval_document")
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload={
                "title": chunk.get("title", ""),
                "content": chunk.get("content", ""),
                "source_label": chunk.get("source_label", "Evoke Endurance Nutrition"),
                "url": chunk.get("url"),
            },
        )
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=COLLECTION_NUTRITION_PRINCIPLES, points=points)
    print(f"[KBRetrieval] Reindexed {len(points)} nutrition principle chunks into {COLLECTION_NUTRITION_PRINCIPLES}")
    return len(points)


def search_principles(
    query: str,
    api_key: str,
    scheduler_k: int = 4,
    nutrition_k: int = 2,
) -> list[dict]:
    """Search scheduler and nutrition principle collections with a single query embedding.

    Tolerates either collection missing. Returns list of hits with title, content, score, ref, domain.
    """
    total_k = scheduler_k + nutrition_k
    active_collections = []
    client = _client()

    has_sched = client.collection_exists(COLLECTION_SCHEDULER)
    has_nutr = client.collection_exists(COLLECTION_NUTRITION_PRINCIPLES)

    if has_sched:
        active_collections.append(COLLECTION_SCHEDULER)
    if has_nutr:
        active_collections.append(COLLECTION_NUTRITION_PRINCIPLES)

    with observability.span(
        "retrieval",
        metadata={"collections": active_collections or [COLLECTION_SCHEDULER], "retrieval_k": total_k},
    ) as retrieval:
        if not has_sched and not has_nutr:
            retrieval.set(grounded=False, chunk_refs=[], chunk_scores=[])
            return []

        vector = _embed([query], api_key, task_type="retrieval_query")[0]
        results: list[dict] = []

        if has_sched and scheduler_k > 0:
            hits_sched = client.query_points(collection_name=COLLECTION_SCHEDULER, query=vector, limit=scheduler_k).points
            for hit in hits_sched:
                if not hit.payload:
                    continue
                title = hit.payload.get("title", "")
                content = hit.payload.get("content", "")
                results.append({
                    "title": title,
                    "content": content,
                    "score": float(hit.score),
                    "ref": _chunk_ref(title, content),
                    "domain": "scheduler",
                    "source_label": hit.payload.get("source_label", "Training for the Uphill Athlete"),
                    "url": hit.payload.get("url"),
                })

        if has_nutr and nutrition_k > 0:
            hits_nutr = client.query_points(collection_name=COLLECTION_NUTRITION_PRINCIPLES, query=vector, limit=nutrition_k).points
            for hit in hits_nutr:
                if not hit.payload:
                    continue
                title = hit.payload.get("title", "")
                content = hit.payload.get("content", "")
                results.append({
                    "title": title,
                    "content": content,
                    "score": float(hit.score),
                    "ref": _chunk_ref(title, content),
                    "domain": "nutrition",
                    "source_label": hit.payload.get("source_label", "Evoke Endurance Nutrition"),
                    "url": hit.payload.get("url"),
                })

        # Sort combined hits by retrieval score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        retrieval.set(
            grounded=bool(results),
            chunk_refs=[r["ref"] for r in results],
            chunk_scores=[r["score"] for r in results],
        )
        return results
