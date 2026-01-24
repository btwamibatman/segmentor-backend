from pydantic import BaseModel

class VideoCreateResponse(BaseModel):
    video_id: int
    status: str