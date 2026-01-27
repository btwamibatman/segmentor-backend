FROM python:3.11-slim

# Устанавливаем системные зависимости (ffmpeg нужен для whisper)
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# СНАЧАЛА копируем только requirements
COPY requirements.txt .

# Устанавливаем библиотеки (этот слой будет качаться долго, но ОДИН раз)
RUN pip install --no-cache-dir -r requirements.txt

# И ТОЛЬКО ПОТОМ копируем весь остальной код
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]