import os
import sqlite3
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
# The current app has only a health check ("/") defined.
from src.api.main import app

# Constants for the database used by the database container
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../minimal-to-do-list-301716-301727/database"))
DB_PATH = os.path.join(DB_DIR, "myapp.db")


@pytest.fixture(scope="session")
def db_exists() -> bool:
    """
    Verify that the SQLite database file exists at the expected path.
    Tests should not mutate this database; write operations are skipped if endpoints are missing.
    """
    return os.path.exists(DB_PATH)


@pytest.fixture(scope="session")
def readonly_db_connection(db_exists: bool) -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a read-only SQLite connection to verify seed data.
    This uses URI mode to open the database in read-only mode.
    """
    if not db_exists:
        pytest.skip("SQLite database file myapp.db not found at expected path; run database/init_db.py first.")

    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        # Ensure foreign keys pragma isn't needed for read-only operations
        yield conn
    finally:
        conn.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    Provide a fresh TestClient per test for isolation.
    """
    with TestClient(app) as c:
        yield c


def test_health_check(client: TestClient):
    """
    Sanity check to ensure the FastAPI app is running.
    """
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Healthy"}


def test_database_file_location_and_seed(db_exists: bool, readonly_db_connection: sqlite3.Connection):
    """
    Verify that the SQLite database path and todos table exist and contains seed rows inserted by init_db.py.
    """
    assert db_exists, f"Database not found at {DB_PATH}"

    cur = readonly_db_connection.cursor()
    # Check that todos table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
    assert cur.fetchone() is not None, "todos table is missing in the SQLite database"

    # Check that seed data exists (init_db.py seeds 2 rows if empty)
    cur.execute("SELECT COUNT(*) FROM todos")
    count = cur.fetchone()[0]
    assert count >= 2, f"Expected at least 2 seeded todos, found {count}"


# The following tests define the expected behavior for CRUD operations.
# Currently, the app does not expose these endpoints; thus, these tests will be xfailed
# with clear messages so that when endpoints are implemented, the xfails can be removed.

@pytest.mark.xfail(reason="Todos list endpoint not implemented: GET /todos")
def test_list_todos(client: TestClient):
    resp = client.get("/todos")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Each item should have id, title, completed, created_at
    if data:
        item = data[0]
        assert {"id", "title", "completed", "created_at"}.issubset(item.keys())


@pytest.mark.xfail(reason="Create todo endpoint not implemented: POST /todos")
def test_create_todo_validation_and_success(client: TestClient):
    # Missing title validation
    resp = client.post("/todos", json={})
    assert resp.status_code in (400, 422)

    # Title is empty
    resp = client.post("/todos", json={"title": ""})
    assert resp.status_code in (400, 422)

    # Valid create
    resp = client.post("/todos", json={"title": "Write tests"})
    assert resp.status_code == 201
    created = resp.json()
    assert created["title"] == "Write tests"
    assert created["completed"] in (False, 0)
    assert "id" in created and isinstance(created["id"], int)


@pytest.mark.xfail(reason="Get todo by id endpoint not implemented: GET /todos/{id}")
def test_get_todo_by_id_and_not_found(client: TestClient):
    # Not found
    resp = client.get("/todos/999999")
    assert resp.status_code == 404

    # After create, can retrieve by id
    created = client.post("/todos", json={"title": "A single todo"}).json()
    todo_id = created["id"]

    resp = client.get(f"/todos/{todo_id}")
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == todo_id
    assert item["title"] == "A single todo"


@pytest.mark.xfail(reason="Full update endpoint not implemented: PUT /todos/{id}")
def test_update_todo_put_validation_and_success(client: TestClient):
    # Create one
    created = client.post("/todos", json={"title": "Original"}).json()
    todo_id = created["id"]

    # Validation: missing fields
    resp = client.put(f"/todos/{todo_id}", json={})
    assert resp.status_code in (400, 422)

    # Success: change title and completed
    resp = client.put(f"/todos/{todo_id}", json={"title": "Updated", "completed": True})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["id"] == todo_id
    assert updated["title"] == "Updated"
    assert updated["completed"] in (True, 1)


@pytest.mark.xfail(reason="Partial update endpoint not implemented: PATCH /todos/{id}")
def test_update_todo_patch_edge_cases(client: TestClient):
    # Create one
    created = client.post("/todos", json={"title": "Patch me"}).json()
    todo_id = created["id"]

    # No body
    resp = client.patch(f"/todos/{todo_id}", json={})
    # decide whether to treat as no-op or 400; accept either 200 or 400/422
    assert resp.status_code in (200, 400, 422)

    # Patch title only
    resp = client.patch(f"/todos/{todo_id}", json={"title": "Patched"})
    assert resp.status_code == 200
    patched = resp.json()
    assert patched["title"] == "Patched"

    # Patch completed only
    resp = client.patch(f"/todos/{todo_id}", json={"completed": True})
    assert resp.status_code == 200
    patched2 = resp.json()
    assert patched2["completed"] in (True, 1)


@pytest.mark.xfail(reason="Delete endpoint not implemented: DELETE /todos/{id}")
def test_delete_todo_and_idempotency(client: TestClient):
    # Create one
    created = client.post("/todos", json={"title": "Delete me"}).json()
    todo_id = created["id"]

    # Delete
    resp = client.delete(f"/todos/{todo_id}")
    assert resp.status_code in (200, 204)

    # Delete again should be 404 or 204 (idempotent)
    resp2 = client.delete(f"/todos/{todo_id}")
    assert resp2.status_code in (204, 404)
