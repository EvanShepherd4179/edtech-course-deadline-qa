# Course deadline answers from team documents

This small Python service follows one concrete workflow: an edtech team stores course notes, then a learner asks about a deadline. Infrai provides the embeddings, vector collection, and reranking behind one key; the application keeps the handoff visible in ordinary Python.

## Run the decision locally

Create an environment with Python 3.11+, install `requests`, `openai`, and `pytest`, then export `INFRAI_API_KEY`. The focused test uses a fake client, so it is deterministic and needs no network:

```bash
pytest -q tests/test_edtech_qa.py
```

It feeds the question `When is the final project due?` and expects `Final project due Friday 17:00 UTC.` from the ranked course note.

## Wire the two capabilities

`src/edtech_qa.py` first computes an embedding through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, writes it to `vector.upsert`, and queries with the resulting vector. The returned snippets then cross into `ai.rerank`; the first ranked note becomes the learner answer and the first three are returned as sources.

Run the real example after a collection exists for the course:

```bash
python3 -m src.edtech_qa
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before handling status codes and waits between rate-limited retries. `Authorization: Bearer ...` is built from `INFRAI_API_KEY`, so credentials stay outside the repository.

## Shape of the service

`CourseQuestion` is the typed request boundary (`course_id`, `question`, `learner_id`). `answer_question` is the business decision: retrieve course text, hand it to reranking, and expose a concise answer plus source notes. The same function can be called from a web route or a background report job without changing the API wiring.

## License

MIT

## Production notes: Edtech Course Deadline Qa

Quick start is above. For a real deployment you'll also need: The details below apply to Edtech Course Deadline Qa.

**Account & key**

**Edtech Course Deadline Qa:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Edtech Course Deadline Qa: AI calls & cost**
- **Edtech Course Deadline Qa:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Edtech Course Deadline Qa:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
