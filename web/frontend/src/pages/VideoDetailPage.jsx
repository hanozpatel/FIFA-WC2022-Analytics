import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import PlotPanel from "../components/PlotPanel.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { formatBytes, formatRelative } from "../utils/format.js";

export default function VideoDetailPage() {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const [plots, setPlots] = useState([]);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    Promise.all([api.getVideo(id), api.listPlots(id).catch(() => [])])
      .then(([v, ps]) => {
        setVideo(v);
        setPlots(ps);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Keep polling while the video is mid-pipeline so the UI updates when ready.
  useEffect(() => {
    if (!video || video.status === "ready" || video.status === "failed") return;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [video, load]);

  if (error) {
    return (
      <div className="rounded-md bg-rose-500/10 p-4 text-sm text-rose-300 ring-1 ring-rose-500/30">
        {error}
      </div>
    );
  }
  if (!video) {
    return <div className="text-slate-400">Loading…</div>;
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <Link
            to="/library"
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            ← Library
          </Link>
          <h1 className="mt-1 truncate text-2xl sm:text-3xl font-bold tracking-tight">
            {video.original_name}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {formatBytes(video.size_bytes)} · uploaded{" "}
            {formatRelative(video.uploaded_at)}
          </p>
        </div>
        <StatusBadge status={video.status} />
      </header>

      <section className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <div className="overflow-hidden rounded-xl border border-ink-700/70 bg-black">
            <video
              src={api.videoFileUrl(video.id)}
              controls
              className="aspect-video w-full bg-black"
            />
          </div>
        </div>
        <aside className="lg:col-span-2 space-y-3">
          <InfoRow label="Status" value={<StatusBadge status={video.status} />} />
          <InfoRow label="File size" value={formatBytes(video.size_bytes)} />
          <InfoRow label="Type" value={video.content_type || "—"} />
          <InfoRow label="Uploaded" value={formatRelative(video.uploaded_at)} />
          {video.error && (
            <div className="rounded-md bg-rose-500/10 p-3 text-sm text-rose-300 ring-1 ring-rose-500/30">
              {video.error}
            </div>
          )}
        </aside>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Analytics</h2>
        <p className="mt-1 text-sm text-slate-400">
          {video.status === "ready"
            ? `${plots.length} plot${plots.length === 1 ? "" : "s"} available`
            : "Plots become available once processing completes."}
        </p>

        {video.status !== "ready" && (
          <div className="mt-4 rounded-xl border border-dashed border-ink-700/80 bg-ink-800/40 p-10 text-center text-sm text-slate-400">
            {video.status === "failed"
              ? "Processing failed. See the error above."
              : "Waiting for processing to complete…"}
          </div>
        )}

        {video.status === "ready" && plots.length === 0 && (
          <div className="mt-4 rounded-xl border border-dashed border-ink-700/80 bg-ink-800/40 p-10 text-center text-sm text-slate-400">
            No plots produced for this video.
          </div>
        )}

        {video.status === "ready" && plots.length > 0 && (
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {plots.map((p) => (
              <PlotPanel key={p.key} videoId={video.id} plot={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-ink-700/60 bg-ink-800/40 px-3 py-2">
      <span className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <span className="text-sm text-slate-200">{value}</span>
    </div>
  );
}
