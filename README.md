# FORM local development — Tasks 1–5

This repository contains the local Django and PostgreSQL foundation, catalog, audited inventory, Django Admin management, storefront search, a session cart, guest COD checkout and order operations.

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

Adding an item to the cart does not place an order or reduce stock. If a product is out of stock or hidden, adding it to the cart is rejected; an item already in the cart is marked unavailable when its stock changes.

## Guest COD checkout (Task 4)

```powershell
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose run --rm web pytest -q
```

From `/cart/`, use **Tiếp tục đặt hàng COD**. Enter a recipient name, phone and address; no customer account is required. A successful checkout creates an order and item snapshots, records one stock movement for each SKU, reduces stock and clears the cart. The shipping fee and total are calculated by the server from **Core → Shop settings**. A repeated submission of the same checkout returns the same order; changing its content with the same request key is rejected.

The confirmation link uses a secret token. Keep it private: anyone with the link can view that order. An order number or phone number alone cannot open it. PostgreSQL stores only the token hash. Customer contact details and tracking tokens are not written to normal web access logs. Do not paste tracking links into public chats or screenshots.

To inspect orders in PostgreSQL without printing customer contact data:

```powershell
docker compose exec db psql -U form -d form -c "SELECT display_number, status, subtotal, shipping_fee, total FROM orders_order ORDER BY id DESC LIMIT 5"
docker compose exec db psql -U form -d form -c "SELECT o.display_number, i.snapshot_sku, i.quantity, i.unit_price, i.line_total FROM orders_orderitem i JOIN orders_order o ON o.id=i.order_id ORDER BY i.id DESC LIMIT 10"
docker compose exec db psql -U form -d form -c "SELECT order_id, variant_id, delta, before, after FROM inventory_stockmovement WHERE order_id IS NOT NULL ORDER BY id DESC LIMIT 10"
```

One fake local browser-check order, `FORM-000001`, was created on SKU `FORM-DEMO-BLK-M`; its demo stock changed from 8 to 7 at checkout.

## Order operations and staff roles (Task 5)

After updating the source, apply migrations and create the staff role groups:

```powershell
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_roles
docker compose run --rm web pytest -q
```

In `/admin/`, open **Orders → Orders**. The order page shows customer details, item snapshots and totals without editable status or price fields. Use **Chuyển trạng thái** to move PENDING → CONFIRMED → SHIPPING → COMPLETED, or cancel while PENDING or CONFIRMED. Cancellation restores stock and records a positive stock movement once; a second cancellation does not restore again. **Order status histories** shows who changed a status, when, and the reason. **Inventory → Stock movements** shows the matching stock adjustment.

The `setup_roles` command creates **Product manager**, **Inventory manager** and **Order manager** groups. Assign a staff account to a group in **Authentication and Authorization → Users**. It is safe to run the command again; it refreshes group permissions without creating users or resetting passwords. A superuser already has all permissions.

Admin login POSTs are limited to 10 per IP and checkout POSTs to 20 per IP in a 15 minute window. Counts are stored in PostgreSQL and shared by web workers. Set `FORM_ADMIN_LOGIN_LIMIT`, `FORM_CHECKOUT_LIMIT` and `FORM_RATE_WINDOW_SECONDS` in `.env` to adjust them; zero for either limit disables that limit. A blocked request returns HTTP 429. The IP comes from the direct connection; forwarded headers are not trusted.

Buyers can reopen their private order tracking link to see the current status. Visiting `/orders/track/` in the same browser session after checkout redirects to the most recent order; without that session, the page explains how to find the saved link. No buyer account or order history list exists in this approved guest checkout scope. Keep the tracking link private.

Check the latest order changes and stock restoration in PostgreSQL without customer contact data:

```powershell
docker compose exec db psql -U form -d form -c "SELECT o.display_number, h.from_status, h.to_status, h.reason, h.created_at FROM orders_orderstatushistory h JOIN orders_order o ON o.id=h.order_id ORDER BY h.id DESC LIMIT 10"
docker compose exec db psql -U form -d form -c "SELECT o.display_number, m.variant_id, m.delta, m.before, m.after FROM inventory_stockmovement m JOIN orders_order o ON o.id=m.order_id ORDER BY m.id DESC LIMIT 10"
```
