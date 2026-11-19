# FORM local development — Task 1

This repository currently contains the local Django and PostgreSQL foundation. Catalog, inventory and checkout are later tasks.

## Start on Windows PowerShell

Docker Desktop must be running with its Linux engine. From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace both placeholder secrets with unique random values. Keep `.env` local; it is ignored by Git. Then:

```powershell
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose run --rm web pytest -q
```

Open <http://localhost:8000/health/live/> and <http://localhost:8000/health/ready/>. Both should return HTTP 200 while the database is running. Admin login is at <http://localhost:8000/admin/>. There is no default admin password. The database is private to the Compose network; only the web port is bound to `127.0.0.1`.

Source code reloads automatically in local development. Ordinary stop/start:

```powershell
docker compose stop
docker compose start
```

Use `docker compose down` when you want to remove containers. Do **not** add `-v` for routine restarts: that removes the named PostgreSQL and media volumes. `postgres_data` holds database records and `media_data` holds uploaded files. Backups and restore tooling are scheduled for Task 6.

## Quick checks

```powershell
docker compose ps
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations
docker compose run --rm web pytest tests/test_health.py -q
```

The test runner creates a separate PostgreSQL test database and does not run against shop data. If port 8000 is busy, stop the other process before starting Compose. If readiness returns 503, inspect `docker compose ps` and `docker compose logs db web`.

Production settings are a separate Django module, but hosting is outside this task. The local Compose service runs Django's development server only.
