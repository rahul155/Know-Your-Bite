import uuid
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult

from app.worker import process_image, celery

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API running"}

# ================= ANALYZE =================
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = f"temp_{file_id}.jpg"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🔥 Only AI (no YOLO shown)
    task = process_image.delay(file_path)

    return {
        "task_id": task.id,
        "status": "processing"
    }

# ================= RESULT =================
@app.get("/result/{task_id}")
def get_result(task_id: str):
    task = AsyncResult(task_id, app=celery)

    if task.state == "SUCCESS":
        return {
            "status": "done",
            "result": task.result
        }

    return {"status": "processing"}