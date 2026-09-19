from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

tasks = [
    {
        "id": 1,
        "title": "Finish assignment",
        "done": False
    },
    {
        "id": 2,
        "title": "Buy groceries",
        "done": False
    },
    {
        "id": 3,
        "title": "Submit project",
        "done": True
    }
]


@app.get("/")
async def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]

    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.get("/tasks")
async def get_tasks():
    return tasks


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


class TaskCreate(BaseModel):
    title: str | None = None


@app.post("/tasks", status_code=201)
async def create_task(body: TaskCreate):
    if body.title is None or body.title.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and cannot be empty"}
        )
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": new_id, "title": body.title.strip(), "done": False}
    tasks.append(task)
    return task
