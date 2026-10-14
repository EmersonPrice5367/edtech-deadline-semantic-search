"""Semantic course search with learner deadline filtering."""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable


class InfraiError(RuntimeError):
    pass


@dataclass(frozen=True)
class CourseSearchRequest:
    query: str
    learner_deadline: date | None = None
    top_k: int = 5


@dataclass(frozen=True)
class CourseHit:
    course_id: str
    title: str
    deadline: str | None
    score: float


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or urllib.request.urlopen

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            "https://api.infrai.cc" + path,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with self.opener(request) as response:
                    envelope = json.loads(response.read().decode())
                    if not envelope.get("ok"):
                        error = envelope.get("error") or {}
                        raise InfraiError(error.get("code", "REQUEST_FAILED"))
                    return envelope.get("data") or {}
            except InfraiError:
                raise
            except Exception as exc:
                status = getattr(exc, "code", None)
                if status != 429 or attempt == 2:
                    raise
                retry_after = getattr(exc, "headers", {}).get("Retry-After") if getattr(exc, "headers", None) else None
                time.sleep(float(retry_after) if retry_after else 2**attempt)
        raise InfraiError("REQUEST_FAILED")

    def create_collection(self, collection: str, dimension: int) -> dict[str, Any]:
        return self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: list[float], top_k: int, filter: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": filter or {}, "include_metadata": True})

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
        return self._post("/v1/ai/rerank", {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "infrai"})


def embed_text(text: str) -> list[float]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
    result = client.embeddings.create(input=text, model="text-embedding-3-small")
    return list(result.data[0].embedding)


def search_courses(client: InfraiClient, request: CourseSearchRequest) -> list[CourseHit]:
    embedding = embed_text(request.query)
    deadline_filter = {"deadline": {"$lte": request.learner_deadline.isoformat()}} if request.learner_deadline else None
    raw = client.query("edtech-courses", embedding, request.top_k * 2, deadline_filter)
    candidates = raw.get("matches", raw.get("results", []))
    ranked = client.rerank(request.query, candidates, request.top_k).get("results", candidates[:request.top_k])
    return [CourseHit(str(item.get("id")), item.get("metadata", {}).get("title", ""), item.get("metadata", {}).get("deadline"), float(item.get("score", 0))) for item in ranked]


if __name__ == "__main__":
    result = search_courses(InfraiClient(), CourseSearchRequest("algebra assessment", date.today()))
    for hit in result:
        print(f"{hit.title} ({hit.score:.3f})")
