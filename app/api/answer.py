from fastapi import APIRouter
from app.schemas.answer import QuizResult

router = APIRouter()

@router.post("/quiz-result")
async def post_quiz_result(result: QuizResult):
    # TODO: Save quiz result to database
    return {"status": "ok"}
