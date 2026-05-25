import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import VideoCard from "../components/VideoCard.jsx";

export default function LibraryPage() {
  const [videos, setVideos] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api
      .listVideos()
      .then(setVideos)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const handleDelete = async (video) => {
    if (!confirm(`Delete "${video.original_name}"? This cannot be undone.`))
      return;
    try {
      await api.deleteVideo(video.id);
      setVideos((vs) => vs.filter((v) => v.id !== video.id));
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div>
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Video library
          </h1>
          <p className="mt-2 text-slate-400">
            {videos == null
              ? "Loading…"
              : `${videos.length} video${videos.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <Link
          to="/upload"
          className="shrink-0 rounded-md bg-accent-600 px-4 py-2 text-sm font-semibold text-white hover:bg-accent-500"
        >
          Upload video
        </Link>
      </header>

      {error && (
        <div className="rounded-md bg-rose-500/10 p-4 text-sm text-rose-300 ring-1 ring-rose-500/30">
          {error}
        </div>
      )}

      {videos && videos.length === 0 && <EmptyState />}

      {videos && videos.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {videos.map((v) => (
            <VideoCard key={v.id} video={v} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed border-ink-700/80 bg-ink-800/40 p-10 text-center">
      <div className="mx-auto h-12 w-12 rounded-full bg-ink-700/60 flex items-center justify-center text-2xl">
        🎬
      </div>
      <h2 className="mt-4 text-lg font-semibold">No videos yet</h2>
      <p className="mt-1 text-sm text-slate-400">
        Upload your first match recording to get started.
      </p>
      <Link
        to="/upload"
        className="mt-4 inline-block rounded-md bg-accent-600 px-4 py-2 text-sm font-semibold text-white hover:bg-accent-500"
      >
        Upload video
      </Link>
    </div>
  );
}
