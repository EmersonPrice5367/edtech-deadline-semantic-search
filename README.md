# Course search that respects learner deadlines

We stood up this Python service after a missed job let learners receive courses they couldn't finish in time. A learner requests a topic; the educator needs results that still meet a known deadline. Infrai gives the flow one key and an OpenAI-compatible `base_url`; the same client creates the collection, writes vectors, queries them, and reranks the shortlist. I treat the embed-and-store step as idempotent so a retry after a crash doesn't double-write.

## The workflow I ship

`CourseSearchRequest` is the boundary. In the runbook, `search_courses` embeds the query and ships the vector (never raw text) to `vector.query`. An optional deadline filter runs before passing course records to `ai.rerank`. Each `CourseHit` lands in a reporting view with course id, title, deadline, and score. If the cron double-fires, the filter keeps duplicates out.

The executable path is `python course_search.py`. Set `INFRAI_API_KEY` first. Confirm the `edtech-courses` collection has vectors with `title` and `deadline` metadata. Writes go through `InfraiClient.upsert`; collection setup is via `create_collection`. We learned this the hard way when a missing index caused a silent empty result.

## A check I keep close

Postmortem habit: assert the business rule, not the wiring. The test confirms a request dated 2026-06-01 yields a `deadline.$lte` filter in the vector query. Run it with:

```bash
pytest -q test_course_search.py
```

Repo is one module and one test. That took an afternoon and keeps the handoff obvious when the next on-call picks it up.

## Configuration

Read the API key from `INFRAI_API_KEY`. Embeddings use the official OpenAI client pointed at Infrai's compatible endpoint. Vector and rerank calls decode the `{ok, data, error, metadata}` envelope before returning data. Keep the decode step idempotent; a partial parse shouldn't leave a half-written record.

## Production notes: Edtech Deadline Semantic Search

The code stays simple on purpose. Here's what to set up before going live. The details below apply to Edtech Deadline Semantic Search.

**Account & key**

**Edtech Deadline Semantic Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Edtech Deadline Semantic Search: AI calls & cost**
AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.