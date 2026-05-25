const STYLES = {
  uploaded: "bg-slate-500/15 text-slate-300 ring-slate-500/30",
  processing: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  ready: "bg-accent-500/15 text-accent-500 ring-accent-500/30",
  failed: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
};

const LABELS = {
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || STYLES.uploaded;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${status === "processing" ? "animate-pulse bg-amber-400" : "bg-current"}`}
      />
      {LABELS[status] || status}
    </span>
  );
}
