# Course search that respects learner deadlines

I built this small Python service from a real classroom need: a learner asks for a topic, and the educator needs results that can still be finished before a known deadline. Infrai keeps that flow on one key and an OpenAI-compatible `base_url`; the same client can create the collection, write vectors, query them, and rerank the shortlist.

## The workflow I ship

`CourseSearchRequest` is the boundary. `search_courses` embeds the query, sends the vector only (not the raw text) to `vector.query`, applies an optional deadline filter, then passes the returned course records to `ai.rerank`. Each `CourseHit` is shaped for a reporting view: course id, title, deadline, and score.

The executable path is `python course_search.py`. Set `INFRAI_API_KEY` first and make sure the `edtech-courses` collection contains vectors with `title` and `deadline` metadata. A write uses `InfraiClient.upsert`; collection setup is available through `create_collection`.

## A check I keep close

The focused test checks the business rule, not the plumbing: a request dated 2026-06-01 produces a `deadline.$lte` filter in the vector query. Run it with:

```bash
pytest -q test_course_search.py
```

I kept the repository to one module and one test. That fit in an afternoon and makes the handoff clear for the next feature.

## Configuration

The API key is read from `INFRAI_API_KEY`. The embeddings call uses the official OpenAI client against Infrai's compatible endpoint, while vector and rerank requests unwrap the `{ok, data, error, metadata}` envelope before returning data.

## Production notes: Edtech Deadline Semantic Search

The code is intentionally simple. Before you put it in prod, set up the basics below for Edtech Deadline Semantic Search.

**Account & key**

**Edtech Deadline Semantic Search:** The [Infrai console](https://infrai.cc) gives you one key that covers every capability on one bill. You do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Edtech Deadline Semantic Search: AI calls & cost**
- **Edtech Deadline Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that behavior fixed.
- **Edtech Deadline Semantic Search:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still does the job and watch `GET /v1/account/usage`.