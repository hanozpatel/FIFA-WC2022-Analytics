import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import UploadPage from "./pages/UploadPage.jsx";
import LibraryPage from "./pages/LibraryPage.jsx";
import VideoDetailPage from "./pages/VideoDetailPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/library" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/videos/:id" element={<VideoDetailPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

function NotFound() {
  return (
    <div className="text-center py-24">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-slate-400">That URL doesn't match anything.</p>
    </div>
  );
}
