import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.video import router
from app.schemas.video import AnswerRequest

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_answer_request_rejects_negative_question_index():
    with pytest.raises(ValidationError):
        AnswerRequest(question_index=-1, answer="A")


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("get", "/video/1/segment/-1/quiz", None),
        (
            "post",
            "/video/1/segment/-1/answer",
            {"question_index": 0, "answer": "A"},
        ),
    ],
)
def test_routes_reject_negative_segment_index(method, path, json_body):
    response = client.request(method, path, json=json_body)

    assert response.status_code == 422


def test_answer_route_rejects_negative_question_index():
    response = client.post(
        "/video/1/segment/0/answer",
        json={"question_index": -1, "answer": "A"},
    )

    assert response.status_code == 422
