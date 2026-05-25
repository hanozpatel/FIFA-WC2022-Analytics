from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOADS_DIR
from .db import connect, init_db
from .plots import get_plot, list_plots
from .schemas import PlotSummary, StatusUpdate, Video

app = FastAPI(title="Soccer Analytics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _row_to_video(row) -> Video:
    return Video(**dict(row))


def _video_path(filename: str) -> Path:
    return UPLOADS_DIR / filename


def _set_status(video_id: str, status: str, error: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status = ?, error = ?, updated_at = datetime('now') WHERE id = ?",
            (status, error, video_id),
        )


async def _simulate_processing(video_id: str) -> None:
    """Demo-only: pretend the analytics pipeline is running.

    Remove this once a real processor is wired up — production status changes
    should come from PATCH /api/videos/{id}/status.
    """
    try:
        await asyncio.sleep(2)
        _set_status(video_id, "processing")
        await asyncio.sleep(4)
        _set_status(video_id, "ready")
    except Exception as e:  # pragma: no cover
        _set_status(video_id, "failed", str(e))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/videos", response_model=List[Video])
def list_videos() -> List[Video]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM videos ORDER BY uploaded_at DESC").fetchall()
    return [_row_to_video(r) for r in rows]


@app.get("/api/videos/{video_id}", response_model=Video)
def get_video(video_id: str) -> Video:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Video not found")
    return _row_to_video(row)


@app.post("/api/videos", response_model=Video, status_code=201)
async def upload_video(file: UploadFile = File(...)) -> Video:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type {ext!r}. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    video_id = uuid.uuid4().hex
    stored_name = f"{video_id}{ext}"
    dest = _video_path(stored_name)

    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(413, "File too large")
                out.write(chunk)
    finally:
        await file.close()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO videos (id, filename, original_name, size_bytes, content_type, status)
            VALUES (?, ?, ?, ?, ?, 'uploaded')
            """,
            (video_id, stored_name, file.filename or stored_name, size, file.content_type),
        )
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()

    # Demo simulation — drop this once a real processing pipeline is wired up.
    asyncio.create_task(_simulate_processing(video_id))

    return _row_to_video(row)


@app.patch("/api/videos/{video_id}/status", response_model=Video)
def update_status(video_id: str, payload: StatusUpdate) -> Video:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Video not found")
        conn.execute(
            "UPDATE videos SET status = ?, error = ?, updated_at = datetime('now') WHERE id = ?",
            (payload.status, payload.error, video_id),
        )
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    return _row_to_video(row)


@app.delete("/api/videos/{video_id}", status_code=204)
def delete_video(video_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Video not found")
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    _video_path(row["filename"]).unlink(missing_ok=True)
    return JSONResponse(status_code=204, content=None)


@app.get("/api/videos/{video_id}/file")
def stream_video(video_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Video not found")
    path = _video_path(row["filename"])
    if not path.exists():
        raise HTTPException(404, "Video file missing on disk")
    return FileResponse(path, media_type=row["content_type"] or "video/mp4", filename=row["original_name"])


@app.get("/api/videos/{video_id}/plots", response_model=List[PlotSummary])
def list_video_plots(video_id: str) -> List[PlotSummary]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Video not found")
    if row["status"] != "ready":
        return []
    return [PlotSummary(key=p.key, title=p.title, description=p.description) for p in list_plots()]


@app.get("/api/videos/{video_id}/plots/{plot_key}")
def get_video_plot(video_id: str, plot_key: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Video not found")
    if row["status"] != "ready":
        raise HTTPException(409, f"Video not ready (status: {row['status']})")
    plot = get_plot(plot_key)
    if not plot:
        raise HTTPException(404, f"Unknown plot {plot_key!r}")
    return plot.compute(_video_path(row["filename"]))
