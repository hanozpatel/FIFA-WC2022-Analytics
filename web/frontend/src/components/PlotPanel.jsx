import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api.js";

const PLOTLY_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#cbd5e1", family: "Inter, sans-serif" },
  margin: { l: 40, r: 20, t: 50, b: 40 },
};

export default function PlotPanel({ videoId, plot }) {
  const [state, setState] = useState({ loading: true, fig: null, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ loading: true, fig: null, error: null });
    api
      .getPlot(videoId, plot.key)
      .then((fig) => !cancelled && setState({ loading: false, fig, error: null }))
      .catch(
        (err) =>
          !cancelled &&
          setState({ loading: false, fig: null, error: err.message })
      );
    return () => {
      cancelled = true;
    };
  }, [videoId, plot.key]);

  return (
    <div className="rounded-xl border border-ink-700/70 bg-ink-800/40 p-4">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <h3 className="font-semibold text-white">{plot.title}</h3>
        {plot.description && (
          <p className="text-xs text-slate-400">{plot.description}</p>
        )}
      </div>
      <div className="min-h-[360px]">
        {state.loading && (
          <div className="flex h-[360px] items-center justify-center text-sm text-slate-400">
            Loading…
          </div>
        )}
        {state.error && (
          <div className="flex h-[360px] items-center justify-center text-sm text-rose-300">
            {state.error}
          </div>
        )}
        {state.fig && (
          <Plot
            data={state.fig.data}
            layout={{ ...state.fig.layout, ...PLOTLY_LAYOUT }}
            config={{ displaylogo: false, responsive: true }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        )}
      </div>
    </div>
  );
}
