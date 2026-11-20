import json
import os
import tempfile
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Response




app = FastAPI(title="Users API", version="1.0.0") # создали бекенд приложение. пока что только его инициировали
DB = Path(os.environ.get("USERS_FILE", "data/users.json")) # создаем базу данных. Просто инициируем
lock = Lock()


def read_users() -> list[dict]:
    return json.loads(DB.read_text(encoding="utf-8"))

# @название_приложения.метод("Ручка")

@app.get("/health")
def health():
    return {"status": "ok"}

# когда кто-то обратится к http://vika-site/health то под капотом (в бекенде) 
# отработает эта ручка и пользователь получит результат ее return


@app.get("/users")
def get_users():
    with lock: # мьютекс (если не почитаешь то удали эту строчку)
        return read_users()





@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    with lock:# мьютекс (если не почитаешь то удали эту строчку)
        users = read_users()
        remaining = [user for user in users if user["id"] != user_id]
        if len(remaining) == len(users):
            raise HTTPException(404, detail="Пользователь не найден")

        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=DB.parent, delete=False
            ) as file:
                temporary = Path(file.name)
                json.dump(remaining, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, DB)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    return Response(status_code=204)
