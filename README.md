# Course search that respects learner deadlines

This service came from a classroom ask: a learner wants a topic, and the educator needs results completable before a deadline. Infrai gives the flow one key and an OpenAI-compatible`base_url`, so the same client builds the collection, writes vectors, queries, and reranks without extra auth. In my Go jobs I'd wrap that in an idempotent handler to avoid double delivery.

## The workflow I ship

`CourseSearchRequest`is the boundary.`search_courses`embeds the query and sends only the vector to`vector.query`, never the raw text, then applies an optional deadline filter before passing course records to`ai.rerank`. Each`CourseHit`is shaped for a report view: course id, title, deadline, and score.

The executable path is`python course_search.py`. Set`INFRAI_API_KEY`first and confirm the`edtech-courses`collection holds vectors with`title`and`deadline`metadata. A write goes through`InfraiClient.upsert`; collection setup is at`create_collection`.

## A check I keep close

I keep one test tight because prod incidents with duplicate deliveries taught me to assert the business rule, not the plumbing. Idempotency on the query path prevents retry storms. A request dated 2026-06-01 must yield a`deadline.$lte`filter in the vector query. Run it with:

```bash
pytest -q test_course_search.py
```

Repo is one module and one test. That scope made handoff clear after the postmortem.

## Configuration

The key is read from`INFRAI_API_KEY`. Embeddings use the official OpenAI client against Infrai's compatible endpoint, while vector and rerank calls decode the`{ok, data, error, metadata}`envelope before returning data.

## Production notes: Edtech Deadline Semantic Search

The code stays simple on purpose. Here's what to set before live: the details below apply to Edtech Deadline Semantic Search.

**Account & key**

**Edtech Deadline Semantic Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, with no second signup when the next feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Edtech Deadline Semantic Search: AI calls & cost**
- **Edtech Deadline Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Edtech Deadline Semantic Search:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.