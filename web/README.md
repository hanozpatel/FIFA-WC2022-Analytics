# Soccer Analytics Web App

A small web app that lets you upload match videos and view Plotly analytics
generated from them. Two-process setup: a FastAPI backend (uploads, SQLite
metadata, plot endpoints) and a React frontend (Vite + Tailwind).

```
web/
├── backend/   FastAPI · SQLite · local uploads/
└── frontend/  React · Vite · Tailwind · Plotly
```

The web layer does **not** run video processing. Each plot endpoint calls a
registered `compute(video_path)` function in `backend/app/plots.py`. Today
those return placeholder figures — wire them to the analytics pipeline when
ready.

---

## Backend

```bash
cd web/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Runs at `http://127.0.0.1:8000`. Uploaded files are stored under
`web/backend/uploads/` and metadata in `web/backend/analytics.db` (both
gitignored).

### API

| Method | Path                              | Purpose                                     |
| ------ | --------------------------------- | ------------------------------------------- |
| GET    | `/api/health`                     | Liveness check                              |
| GET    | `/api/videos`                     | List all videos                             |
| POST   | `/api/videos`                     | Upload a video (multipart `file`)           |
| GET    | `/api/videos/{id}`                | Get one video                               |
| DELETE | `/api/videos/{id}`                | Delete a video + its file                   |
| PATCH  | `/api/videos/{id}/status`         | Update status (`uploaded`/`processing`/`ready`/`failed`) — used by the processor |
| GET    | `/api/videos/{id}/file`           | Stream the raw video                        |
| GET    | `/api/videos/{id}/plots`          | List available plot keys/titles             |
| GET    | `/api/videos/{id}/plots/{key}`    | Plotly figure as JSON                       |

Status state machine: `uploaded → processing → ready` (or `failed`). The
backend never advances the status itself — your processing pipeline does that
via the `PATCH` endpoint.

### Adding a real plot

Open `backend/app/plots.py` and replace the placeholder `_shot_map` (etc.)
with code that returns `json.loads(fig.to_json())` for a real Plotly figure.
To add a new plot, register a `PlotDef(...)` in `_REGISTRY`.

---

## Frontend

```bash
cd web/frontend
npm install
npm run dev
```

Runs at `http://127.0.0.1:5173`. Vite proxies `/api/*` to the backend on
`:8000`, so both must be running.

Pages:
- `/library` — grid of all uploaded videos, polled every 5 s
- `/upload` — drag-and-drop with per-file progress
- `/videos/:id` — video player + auto-discovered Plotly panels

---

## End-to-end flow

1. User uploads a video → backend writes file to `uploads/`, inserts row with
   `status='uploaded'`.
2. Your processing pipeline picks up the file (out of scope here), updates
   status via `PATCH /api/videos/{id}/status` to `processing` then `ready`.
3. When status hits `ready`, the detail page renders one `PlotPanel` per
   registered plot — each one fetches its Plotly JSON on demand.
