from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small to-do list API with full CRUD, stored in memory."
)

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


class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/")
async def root():
    """Describe this API and list its main endpoint."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
async def health():
    """Check that the server is alive."""
    return {
        "status": "ok"
    }


@app.get("/tasks")
async def get_tasks():
    """Return the full list of tasks."""
    return tasks


@app.get(
    "/tasks/{task_id}",
    responses={404: {"description": "Task not found"}}
)
async def get_task(task_id: int):
    """Return a single task by its id."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


@app.post(
    "/tasks",
    status_code=201,
    responses={400: {"description": "Title is missing or empty"}}
)
async def create_task(body: TaskCreate):
    """Create a new task from a title. New tasks start as not done."""
    if body.title is None or body.title.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and cannot be empty"}
        )
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": new_id, "title": body.title.strip(), "done": False}
    tasks.append(task)
    return task


@app.put(
    "/tasks/{task_id}",
    responses={
        400: {"description": "Body is empty or title is empty"},
        404: {"description": "Task not found"}
    }
)
async def update_task(task_id: int, body: TaskUpdate):
    """Update a task's title and/or done status."""
    for task in tasks:
        if task["id"] == task_id:
            if body.title is None and body.done is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "provide title and/or done"}
                )
            if body.title is not None:
                if body.title.strip() == "":
                    return JSONResponse(
                        status_code=400,
                        content={"error": "title cannot be empty"}
                    )
                task["title"] = body.title.strip()
            if body.done is not None:
                task["done"] = body.done
            return task
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    responses={404: {"description": "Task not found"}}
)
async def delete_task(task_id: int):
    """Delete a task by its id."""
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return Response(status_code=204)
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )
