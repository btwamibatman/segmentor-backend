# SegMentor Backend

FastAPI backend for video segmentation, quizzes, and answers.

## Requirements
- Python 3.12+
- ffmpeg / ffprobe installed and доступен в PATH (нужно для извлечения аудио)

## Local Run
1. Create and activate a virtual environment.
2. Install dependencies from requirements.txt.
3. Run the server with uvicorn.

Open Swagger UI at /docs.

### Optional Access Token
If you want to protect endpoints, set ACCESS_TOKEN and pass X-Access-Token header.

## Docker
Build and run using Docker. The container exposes port 8000.

## API Endpoints (minimum)
- POST /video/upload
- GET  /video/{id}/segments
- GET  /segment/{id}/quiz
- POST /segment/{id}/answer

### Access Control & Locks
- Для контроля доступа можно задать ACCESS_TOKEN.
- Сегменты блокируются, пока пользователь не ответит правильно на предыдущие сегменты.

### Notes
- Видео обрабатываются асинхронно в background task.
- Для работы квизов нужен доступ к модели Llama-2 (через HUGGINGFACE_TOKEN).
