import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge.jsx";
import { formatBytes, formatRelative } from "../utils/format.js";

export default function VideoCard({ video, onDelete }) {
  return (
    <div className="group rounded-xl border border-ink-700/70 bg-ink-800/60 p-4 transition hover:border-ink-700 hover:bg-ink-800">
      <div className="flex items-start justify-between gap-3">
        <Link to={`/videos/${video.id}`} className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-white group-hover:text-accent-500">
            {video.original_name}
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            {formatBytes(video.size_bytes)} · uploaded {formatRelative(video.uploaded_at)}
          </p>
        </Link>
        <StatusBadge status={video.status} />
      </div>
      {video.error ? (
        <p className="mt-3 text-xs text-rose-300 line-clamp-2">{video.error}</p>
      ) : null}
      <div className="mt-4 flex items-center justify-between">
        <Link
          to={`/videos/${video.id}`}
          className="text-sm font-medium text-accent-500 hover:text-accent-600"
        >
          Open →
        </Link>
        <button
          onClick={() => onDelete(video)}
          className="text-xs text-slate-400 hover:text-rose-300"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
