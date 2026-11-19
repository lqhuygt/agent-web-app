# FORM local development — Tasks 1–3

This repository contains the local Django and PostgreSQL foundation, catalog, audited inventory, Django Admin management, storefront search and a session cart. Checkout is a later task.

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

## Catalog and inventory (Task 2)

After pulling Task 2 changes, apply migrations and load the optional demo product:

```powershell
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
docker compose run --rm web pytest -q
```

`seed_demo` creates one marked demo trouser product with black and navy colors, M and L sizes, and initial stock. It can be run again without duplicating those records or replacing prices and quantities you edited. It creates no admin account or default password. Demo prices and stock are for local testing only.

In `/admin/`, manage categories and products under **Catalog**. Product pages allow variants and JPEG, PNG or WebP images up to 5 MiB. Under **Inventory → Stocks**, use **Adjust stock** and enter a signed quantity change and reason; the movement appears in **Stock movements**. Quantity and movement records cannot be edited directly in Admin. Staff must have the `inventory | stock | Can adjust stock` permission; the superuser already has it. The **low stock** filter uses each SKU's threshold. Shop shipping fee and free-shipping threshold live under **Core → Shop settings**.

## Storefront and cart (Task 3)

After updating the source, run migrations and restart web if needed:

```powershell
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose run --rm web pytest -q
```

Open `/` for the storefront, `/products/` for search and filters, and `/cart/` for your session cart. Search ignores Vietnamese accents, letter case and repeated spaces. Price filters accept whole, nonnegative VND values. The cart holds at most 10 units of each variant and checks current stock. Price and availability are read from PostgreSQL again when the cart is displayed. Cart forms work with normal page loads; the vendored HTMX 2.0.11 library updates the cart region in place when JavaScript is available. The library source is `https://cdn.jsdelivr.net/npm/htmx.org@2.0.11/dist/htmx.min.js`; its license is in `static/js/LICENSE.htmx.txt`.

Task 3 does not place orders or reduce stock. COD checkout is Task 4. If a product is out of stock or hidden, adding it to the cart is rejected; an item already in the cart is marked unavailable when its stock changes.
