from src.edtech_qa import Answer, CourseQuestion, answer_question


class FakeClient:
    def query(self, collection, question, top_k=5):
        return [{"metadata": {"text": "Final project due Friday 17:00 UTC."}}]

    def rerank(self, question, candidates, top_k=3):
        return candidates


def test_deadline_answer_uses_ranked_course_note():
    result = answer_question(FakeClient(), CourseQuestion("python-101", "When is the final project due?", "learner-7"))
    assert isinstance(result, Answer)
    assert result.text == "Final project due Friday 17:00 UTC."
    assert result.sources == [result.text]
