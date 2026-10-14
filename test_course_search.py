from datetime import date
import course_search


def test_deadline_is_sent_to_vector_query(monkeypatch):
    seen = {}
    monkeypatch.setattr(course_search, "embed_text", lambda _: [0.1, 0.2])
    client = course_search.InfraiClient(api_key="test", opener=lambda request: None)
    client.query = lambda collection, embedding, top_k, filter=None: seen.update(filter=filter) or {"matches": []}
    client.rerank = lambda query, candidates, top_k: {"results": []}
    course_search.search_courses(client, course_search.CourseSearchRequest("fractions", date(2026, 6, 1)))
    assert seen["filter"] == {"deadline": {"$lte": "2026-06-01"}}
