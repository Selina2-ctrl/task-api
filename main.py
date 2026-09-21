from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasks.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Finish assignment", 0),
                    ("Buy groceries", 0),
                    ("Submit project", 1),
                ],
            )
    conn.close()


init_db()

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small to-do list API with full CRUD, stored in memory."
)


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


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
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [row_to_task(row) for row in rows]


@app.get(
    "/tasks/{task_id}",
    responses={404: {"description": "Task not found"}}
)
async def get_task(task_id: int):
    """Return a single task by its id."""
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?",
                       (task_id,)).fetchone()
    conn.close()
    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )
    return row_to_task(row)


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
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (body.title.strip(), 0)
        )
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM tasks WHERE id = ?",
                       (new_id,)).fetchone()
    conn.close()
    return row_to_task(row)


@app.put(
    "/tasks/{task_id}",
    responses={
        400: {"description": "Body is empty or title is empty"},
        404: {"description": "Task not found"}
    }
)
async def update_task(task_id: int, body: TaskUpdate):
    """Update a task's title and/or done status."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return JSONResponse(
                status_code=404,
                content={"error": f"Task {task_id} not found"}
            )
        if body.title is None and body.done is None:
            return JSONResponse(
                status_code=400,
                content={"error": "provide title and/or done"}
            )
        if body.title is not None and body.title.strip() == "":
            return JSONResponse(
                status_code=400,
                content={"error": "title cannot be empty"}
            )
        new_title = body.title.strip(
        ) if body.title is not None else row["title"]
        new_done = int(body.done) if body.done is not None else row["done"]
        with conn:
            conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (new_title, new_done, task_id)
            )
        updated = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return row_to_task(updated)
    finally:
        conn.close()


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    responses={404: {"description": "Task not found"}}
)
async def delete_task(task_id: int):
    """Delete a task by its id."""
    conn = get_db()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            return JSONResponse(
                status_code=404,
                content={"error": f"Task {task_id} not found"}
            )
        return Response(status_code=204)
    finally:
        conn.close()
