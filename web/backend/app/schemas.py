from typing import Optional, Literal
from pydantic import BaseModel

VideoStatus = Literal["uploaded", "processing", "ready", "failed"]


class Video(BaseModel):
    id: str
    filename: str
    original_name: str
    size_bytes: int
    content_type: Optional[str] = None
    status: VideoStatus
    error: Optional[str] = None
    uploaded_at: str
    updated_at: str


class StatusUpdate(BaseModel):
    status: VideoStatus
    error: Optional[str] = None


class PlotSummary(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
