import { useCallback, useRef, useState } from "react";
import { api } from "../api.js";
import { formatBytes } from "../utils/format.js";

const ACCEPT = ".mp4,.mov,.mkv,.avi,.webm";

export default function UploadDropzone({ onUploaded }) {
  const [dragOver, setDragOver] = useState(false);
  const [queue, setQueue] = useState([]); // {file, progress, status, error, video}
  const inputRef = useRef(null);

  const startUpload = useCallback(
    async (file) => {
      const id = `${file.name}-${file.size}-${file.lastModified}`;
      setQueue((q) => [
        ...q.filter((it) => it.id !== id),
        { id, file, progress: 0, status: "uploading", error: null, video: null },
      ]);
      try {
        const video = await api.uploadVideo(file, {
          onProgress: (p) =>
            setQueue((q) =>
              q.map((it) => (it.id === id ? { ...it, progress: p } : it))
            ),
        });
        setQueue((q) =>
          q.map((it) =>
            it.id === id ? { ...it, status: "done", progress: 1, video } : it
          )
        );
        onUploaded?.(video);
      } catch (err) {
        setQueue((q) =>
          q.map((it) =>
            it.id === id ? { ...it, status: "error", error: err.message } : it
          )
        );
      }
    },
    [onUploaded]
  );

  const handleFiles = (fileList) => {
    [...fileList].forEach((f) => startUpload(f));
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={[
          "cursor-pointer rounded-2xl border-2 border-dashed p-10 sm:p-14 text-center transition",
          dragOver
            ? "border-accent-500 bg-accent-500/5"
            : "border-ink-700 bg-ink-800/40 hover:bg-ink-800/70",
        ].join(" ")}
      >
        <div className="mx-auto h-12 w-12 rounded-full bg-ink-700/70 flex items-center justify-center text-2xl">
          ⬆
        </div>
        <p className="mt-4 text-base font-medium text-white">
          Drop a match video here, or click to select
        </p>
        <p className="mt-1 text-sm text-slate-400">
          MP4, MOV, MKV, AVI, WEBM · up to 2 GB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {queue.length > 0 && (
        <ul className="mt-6 space-y-3">
          {queue.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-ink-700/70 bg-ink-800/60 p-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">
                    {item.file.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {formatBytes(item.file.size)}
                  </p>
                </div>
                <span className="shrink-0 text-xs text-slate-300">
                  {item.status === "uploading" &&
                    `${Math.round(item.progress * 100)}%`}
                  {item.status === "done" && "Uploaded"}
                  {item.status === "error" && "Failed"}
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
                <div
                  className={[
                    "h-full transition-all",
                    item.status === "error"
                      ? "bg-rose-500"
                      : item.status === "done"
                        ? "bg-accent-500"
                        : "bg-accent-600",
                  ].join(" ")}
                  style={{ width: `${Math.max(item.progress, 0.02) * 100}%` }}
                />
              </div>
              {item.error && (
                <p className="mt-2 text-xs text-rose-300">{item.error}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
