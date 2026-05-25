import { NavLink, Outlet } from "react-router-dom";

const linkClass = ({ isActive }) =>
  [
    "px-3 py-2 rounded-md text-sm font-medium transition",
    isActive
      ? "bg-ink-700 text-white"
      : "text-slate-300 hover:bg-ink-800 hover:text-white",
  ].join(" ");

export default function Layout() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-ink-700/60 bg-ink-800/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <NavLink to="/library" className="flex items-center gap-2 group">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-accent-600/20 text-accent-500 font-bold">
              ⚽
            </span>
            <span className="font-semibold tracking-tight group-hover:text-white">
              Soccer Analytics
            </span>
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavLink to="/library" className={linkClass}>
              Library
            </NavLink>
            <NavLink to="/upload" className={linkClass}>
              Upload
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <Outlet />
        </div>
      </main>
      <footer className="border-t border-ink-700/60 py-4 text-center text-xs text-slate-500">
        Soccer analytics over uploaded video · local demo
      </footer>
    </div>
  );
}
