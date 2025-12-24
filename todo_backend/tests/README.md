# Todos API Tests

This folder contains tests for the FastAPI backend. Currently, the app only exposes a health check at `/`. The CRUD endpoints for todos are not implemented yet; therefore, CRUD tests are marked with `@pytest.mark.xfail` so they won't fail CI until the endpoints are added.

Expected endpoints and behaviors:
- GET /todos -> 200 OK, returns list[Todo]
- GET /todos/{id} -> 200 OK with item or 404
- POST /todos -> 201 Created with body {"title": str}; validates non-empty title; default completed false/0
- PUT /todos/{id} -> 200 OK with full update {"title": str, "completed": bool}
- PATCH /todos/{id} -> 200 OK with partial update
- DELETE /todos/{id} -> 200/204; deleting again returns 204 or 404

Database integration:
- Use the existing SQLite file at minimal-to-do-list-301716-301727/database/myapp.db created by database/init_db.py.
- Table: todos(id INTEGER PRIMARY KEY, title TEXT NOT NULL, completed INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

Implementation note (to pass tests):
- Add a router to src/api/main.py mounting these routes.
- Use sqlite3; ensure connections read/write to the file path above.
- Convert completed INTEGER (0/1) to bool in API responses for consistency (tests accept either).
