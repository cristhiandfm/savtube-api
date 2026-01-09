from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"

TEMP_DIR = "/tmp/videos"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.post("/api/media/info")
async def get_info(request: DownloadRequest):
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(request.url, download=False)
    return {
        "title": info.get("title"),
        "duration": info.get("duration"),
        "formats": [f["format_id"] for f in info.get("formats", [])]
    }

@app.post("/api/media/download")
async def download(request: DownloadRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    filepath = os.path.join(TEMP_DIR, f"{job_id}.{request.format}")

    def task():
        ydl_opts = {
            "outtmpl": filepath,
            "format": "bestvideo+bestaudio/best" if request.format == "mp4" else "bestaudio/best",
            "merge_output_format": request.format
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

    background_tasks.add_task(task)

    return {"job_id": job_id, "file_url": f"/api/media/file/{job_id}.{request.format}"}

@app.get("/api/media/file/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(TEMP_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    return {"error": "File not found"}
