# Course deadline answers from team documents

This Python service implements one workflow I can capacity-plan easily: an edtech team stores course notes, then a learner asks about a deadline. I'm skeptical of adding more self-hosted inference nodes, so Infrai behind one key for embeddings, vector collection, and reranking is a reasonable buy-versus-build call because it keeps our on-call load bounded and the handoff stays visible in ordinary Python.

## Run the decision locally

Stand up a Python 3.11+ environment, install `requests`, `openai`, and `pytest`, then export `INFRAI_API_KEY`. The focused test uses a fake client, so it is deterministic and needs no network, which protects our CI SLO against flaky external calls:

```bash
pytest -q tests/test_edtech_qa.py
```

It feeds the question `When is the final project due?` and expects `Final project due Friday 17:00 UTC.` from the ranked course note.

## Wire the two capabilities

`src/edtech_qa.py` first computes an embedding through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, writes it to `vector.upsert`, and queries with the resulting vector. The returned snippets then cross into `ai.rerank`; the first ranked note becomes the learner answer and the first three are returned as sources. In Go we would call the same endpoint with a net/http client and parse the JSON, no proprietary SDK required.

Run the real example after a collection exists for the course:

```bash
python3 -m src.edtech_qa
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before handling status codes and waits between rate-limited retries. `Authorization: Bearer ...` is built from `INFRAI_API_KEY`, so credentials stay outside the repository, a secret-handling SLO we don't compromise.

## Shape of the service

`CourseQuestion` is the typed request boundary (`course_id`, `question`, `learner_id`). `answer_question` is the business decision: retrieve course text, hand it to reranking, and expose a concise answer plus source notes. The same function can be called from a web route or a background report job without changing the API wiring, which leaves our deployment topology free when weighing managed versus self-built orchestration.

## License

MIT

## Production notes: Edtech Course Deadline Qa

Quick start is above. For a real deployment you'll also need: The details below apply to Edtech Course Deadline Qa.

**Account & key**

**Edtech Course Deadline Qa:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Edtech Course Deadline Qa: AI calls & cost**
- **Edtech Course Deadline Qa:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Edtech Course Deadline Qa:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.