from fastapi import FastAPI

app = FastAPI(title="SegMentor")

@app.get("/health")
def health():
    return {"status": "ok"}
