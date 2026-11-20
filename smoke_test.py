"""Run with: docker run --rm -i fastapi-server python - < smoke_test.py"""

import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def request(path, method="GET"):
    try:
        with urllib.request.urlopen(
            urllib.request.Request("http://127.0.0.1:8083" + path, method=method),
            timeout=2,
        ) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "users.json"
    initial = [{"id": 1, "name": "Арсений"}, {"id": 2, "name": "Иван"}]
    database.write_text(json.dumps(initial), encoding="utf-8")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8083"],
        env={**os.environ, "USERS_FILE": str(database)},
    )
    try:
        for attempt in range(100):
            try:
                assert request("/health")[0] == 200
                break
            except (OSError, urllib.error.URLError):
                if process.poll() is not None:
                    raise RuntimeError("Server exited before startup")
                time.sleep(0.1)
        else:
            raise RuntimeError("Server did not start")

        assert json.loads(request("/users")[1]) == initial
        status, docs = request("/docs")
        assert status == 200 and b"swagger-ui" in docs
        schema = json.loads(request("/openapi.json")[1])
        assert "/users/{user_id}" in schema["paths"]
        assert request("/users/1", "DELETE") == (204, b"")
        assert json.loads(request("/users")[1]) == [initial[1]]
        assert json.loads(database.read_text()) == [initial[1]]
        assert request("/users/1", "DELETE")[0] == 404
        assert request("/users/invalid", "DELETE")[0] == 422
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: request("/users/2", "DELETE")[0], range(16)))
        assert statuses.count(204) == 1 and statuses.count(404) == 15
        assert json.loads(request("/users")[1]) == []
        assert json.loads(database.read_text()) == []
        print("PASS: health, users, Swagger, OpenAPI, delete, persistence, 404, 422, concurrent deletes")
    finally:
        process.terminate()
        process.wait(timeout=5)
