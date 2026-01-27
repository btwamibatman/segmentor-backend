# SegMentor Backend

AI Video Topic Segmentation & In-Video Quiz Backend

## Features

- **Video Upload**: Accept MP4/MKV/MOV/AVI files
- **ASR**: Speech-to-text with timestamps using Whisper
- **Topic Segmentation**: LLM-powered automatic topic detection
- **Quiz Generation**: Multiple choice, true/false, short answer questions
- **REST API**: FastAPI with OpenAPI/Swagger
- **Database**: SQLite with SQLAlchemy
- **Docker Support**: Easy deployment

## Quick Start

### Local Setup

1. **Clone & Install**:
   ```bash
   git clone <repo-url>
   cd backend
   pip install -r requirements.txt
   ```

2. **Set Environment**:
   ```bash
   export HF_TOKEN=your_huggingface_token
   ```

3. **Run Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   API available at: http://localhost:8000

### Docker Setup

```bash
docker-compose up --build
```

## API Endpoints

### Video Management
- `POST /video/upload` - Upload video file
  - Returns: `{"video_id": int, "status": "queued"}`

- `GET /video/{video_id}/segments` - Get topic segments
  - Returns: List of segments with titles, summaries, keywords

### Quiz System
- `GET /video/{video_id}/segment/{segment_index}/quiz` - Get quiz for segment
  - Returns: Quiz with questions and options

- `POST /video/{video_id}/segment/{segment_index}/answer` - Submit answer
  - Body: `{"question_index": int, "answer": str|int|bool}`
  - Returns: `{"correct": bool, "feedback": str}`

## Architecture

```
Video Upload → Audio Extraction (ffmpeg) → ASR (Whisper) → LLM Segmentation (Qwen 1.5B) → Quiz Generation → API Response
```

- **Models**: Qwen/Qwen2.5-1.5B-Instruct (4-bit quantized)
- **ASR**: Faster-Whisper (small model)
- **Framework**: FastAPI + SQLAlchemy
- **Storage**: SQLite (auto-created)

## Requirements

- Python 3.11+
- ffmpeg (for audio extraction)
- HuggingFace token (for LLM access)
- 6GB+ GPU recommended (for LLM inference)

## Project Structure

```
backend/
├── app/
│   ├── ai/llm/          # Quiz & segmentation LLMs
│   ├── api/             # FastAPI routes
│   ├── core/            # Config, logger
│   ├── db/              # Database models
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic
├── data/                # Uploaded files & DB
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker compose
└── requirements.txt     # Dependencies
```

## Development

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: GET /health
- **Logs**: Check terminal for LLM responses and errors

## Hackathon Deliverables

- ✅ REST API with segmentation & quiz endpoints
- ✅ LLM-powered topic segmentation
- ✅ In-video quiz generation
- ✅ Docker containerization
- ✅ Production-ready code

**Browser Extension**: Implemented separately (not included in this repo).

## License

MIT License