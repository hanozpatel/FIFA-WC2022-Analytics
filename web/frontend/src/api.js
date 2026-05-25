const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* noop */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listVideos: () => request("/videos"),
  getVideo: (id) => request(`/videos/${id}`),
  deleteVideo: (id) => request(`/videos/${id}`, { method: "DELETE" }),
  setStatus: (id, status, error = null) =>
    request(`/videos/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, error }),
    }),
  listPlots: (id) => request(`/videos/${id}/plots`),
  getPlot: (id, key) => request(`/videos/${id}/plots/${key}`),

  uploadVideo: (file, { onProgress } = {}) =>
    new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const fd = new FormData();
      fd.append("file", file);
      xhr.open("POST", `${BASE}/videos`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(e.loaded / e.total);
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          let detail = xhr.statusText;
          try {
            detail = JSON.parse(xhr.responseText).detail || detail;
          } catch {
            /* noop */
          }
          reject(new Error(detail));
        }
      };
      xhr.onerror = () => reject(new Error("Network error"));
      xhr.send(fd);
    }),

  videoFileUrl: (id) => `${BASE}/videos/${id}/file`,
};
