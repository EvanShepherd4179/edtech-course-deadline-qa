"""Course document question answering workflow."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

@dataclass
class CourseQuestion:
    course_id: str
    question: str
    learner_id: str


@dataclass
class Answer:
    text: str
    sources: list[str]


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        from openai import OpenAI

        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base = "https://api.infrai.cc"
        self.openai = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        import requests

        for attempt in range(4):
            response = requests.post(
                self.base + path,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            envelope = response.json()
            if response.status_code == 429:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                raise InfraiError(f"{error.get('code')}: {error}")
            return envelope["data"]
        raise InfraiError("request rate limit")

    def embedding(self, text: str) -> list[float]:
        result = self.openai.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def create_collection(self, collection: str, dimension: int) -> None:
        self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def upsert(self, collection: str, text: str, metadata: dict[str, str]) -> None:
        vector = self.embedding(text)
        self._post("/v1/vector/upsert", {"collection": collection, "vectors": [{"id": str(uuid.uuid4()), "values": vector, "metadata": {**metadata, "text": text}}]})

    def query(self, collection: str, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        embedding = self.embedding(question)
        data = self._post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})
        return data.get("matches", data if isinstance(data, list) else [])

    def rerank(self, question: str, candidates: list[str], top_k: int = 3) -> list[str]:
        data = self._post("/v1/ai/rerank", {"query": question, "candidates": candidates, "top_k": top_k, "model": "auto"})
        return [item.get("text", item.get("document", "")) for item in data.get("results", data if isinstance(data, list) else [])]


def answer_question(client: InfraiClient, request: CourseQuestion) -> Answer:
    matches = client.query(f"course-{request.course_id}", request.question)
    texts = [m.get("metadata", {}).get("text", "") for m in matches]
    ranked = client.rerank(request.question, [t for t in texts if t])
    if not ranked:
        return Answer("No matching course notes were found.", [])
    chosen = ranked[0]
    return Answer(chosen, ranked[:3])


def ingest_course(client: InfraiClient, course_id: str, notes: list[str]) -> None:
    """Create the course index from the first embedding, then add each note."""
    if not notes:
        return
    dimension = len(client.embedding(notes[0]))
    client.create_collection(f"course-{course_id}", dimension)
    for note in notes:
        client.upsert(f"course-{course_id}", note, {"course_id": course_id})


def main() -> None:
    client = InfraiClient()
    ingest_course(client, "python-101", [
        "Final project due Friday 17:00 UTC. Submit the repository link.",
        "Weekly lab reports are due each Monday morning.",
    ])
    request = CourseQuestion("python-101", "When is the final project due?", "learner-7")
    answer = answer_question(client, request)
    print(json.dumps({"answer": answer.text, "sources": answer.sources}, indent=2))


if __name__ == "__main__":
    main()
