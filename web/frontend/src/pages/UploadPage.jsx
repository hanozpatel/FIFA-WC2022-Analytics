import { useNavigate } from "react-router-dom";
import UploadDropzone from "../components/UploadDropzone.jsx";

export default function UploadPage() {
  const navigate = useNavigate();
  return (
    <div className="max-w-3xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Upload a match video
        </h1>
        <p className="mt-2 text-slate-400">
          Drop a recording and we'll process it for analytics. Plots become
          available on the video's detail page once processing completes.
        </p>
      </header>
      <UploadDropzone
        onUploaded={(video) => {
          // After the first successful upload, jump straight to its detail page.
          navigate(`/videos/${video.id}`);
        }}
      />
    </div>
  );
}
