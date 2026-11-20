# Users API

Простой FastAPI-сервер с JSON вместо базы данных.

## Запуск

Нужен запущенный Docker Desktop.

```bash
cd ~/Downloads/fastapi-server
docker compose up -d --build
```

Swagger: http://localhost:8082/docs

JSON хранится в `data/users.json` на хосте, удаления сохраняются после
пересоздания контейнера. Запускайте один экземпляр сервера с одним worker:
блокировка JSON действует внутри одного процесса.

## Проверка

```bash
curl -i http://localhost:8082/health
curl http://localhost:8082/users
curl -i -X DELETE http://localhost:8082/users/1
```

`GET /health` возвращает 200, `GET /users` — весь массив из JSON,
`DELETE /users/{user_id}` — 204 либо 404, если пользователя нет.

Изолированная проверка API, Swagger и параллельных удалений (на временном JSON):

```bash
docker run --rm -i fastapi-server python - < smoke_test.py
```

## Управление

```bash
docker compose logs -f
docker compose down
```

## Перенос в домашний каталог

Если каталог `~/fastapi-server` ещё не существует:

```bash
mv ~/Downloads/fastapi-server ~/fastapi-server
cd ~/fastapi-server
docker compose up -d --build
```

## Без Compose

```bash
docker build -t fastapi-server .
docker run -d --name fastapi-server -p 8082:8082 \
  --mount type=bind,source="$PWD/data",target=/app/data fastapi-server
```

Это учебный локальный сервер без авторизации.


если нужно просто запустить без докера пиши

```
uvicorn main:app --host 0.0.0.0 --port 8067 --workers 1
```