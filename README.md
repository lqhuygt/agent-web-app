# FORM — chạy local từ một máy Windows mới

FORM là cửa hàng một người bán dùng Django, HTMX và PostgreSQL. Source hiện có Task 1–5: quản trị sản phẩm và kho, cửa hàng, giỏ hàng theo session, đặt hàng COD không cần tài khoản, theo dõi và xử lý đơn. Task 6 trong [kế hoạch](docs/superpowers/plans/FORM_Project_Plan_v1.md) chưa triển khai. [Bàn giao cho phiên Codex mới](docs/HANDOFF_CODEX.md) ghi các quyết định và hiện trạng.

## 1. Chuẩn bị

- Máy Windows có Git và Docker Desktop; bật **Linux containers** và chờ Docker Engine chạy.
- Cổng `127.0.0.1:8000` còn trống. PostgreSQL chỉ nằm trong mạng Docker, không mở cổng ra máy ngoài.
- Mở **PowerShell** trong thư mục muốn lưu project. Các lệnh dưới đây chạy trên máy host, không chạy trong WSL.

## 2. Lấy source và tạo cấu hình riêng

```powershell
git clone -b task1-local https://github.com/lqhuygt/agent-web-app.git
Set-Location agent-web-app
Copy-Item .env.example .env
notepad .env
```

Trong `.env`, thay `DJANGO_SECRET_KEY` và `POSTGRES_PASSWORD` mẫu bằng hai giá trị ngẫu nhiên, dài và khác nhau; không để nguyên chữ `replace-with-...`. Giữ `.env` trên máy cá nhân, không commit hoặc gửi qua chat. Các giá trị `POSTGRES_DB=form`, `POSTGRES_USER=form` và `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` dùng được cho localhost. Các biến `FORM_*_LIMIT` ở cuối file là giới hạn lượt thử có thể tùy chỉnh sau.

Máy mới tạo **database và media volume mới**. Source trên GitHub không chứa đơn hàng, tài khoản quản trị, ảnh tải lên hoặc `.env` của máy cũ. Nếu bạn chỉ cần chạy lại từ đầu thì không phải chuyển dữ liệu.

## 3. Khởi động và khởi tạo database

```powershell
docker compose up -d --build
docker compose ps
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_roles
docker compose exec web python manage.py createsuperuser
```

Lệnh `createsuperuser` hỏi tên đăng nhập, email và mật khẩu; tự đặt mật khẩu, không có tài khoản mặc định. `setup_roles` tạo các nhóm **Product manager**, **Inventory manager**, **Order manager**; chạy lại được mà không tạo lại user. Nếu muốn có sản phẩm mẫu để thử luồng mua, chạy thêm:

```powershell
docker compose exec web python manage.py seed_demo
```

`seed_demo` tạo sản phẩm quần mẫu với các biến thể màu/size và tồn ban đầu. Có thể chạy lại mà không ghi đè giá hoặc số lượng đã sửa. Trong Admin, đặt phí giao hàng tại **Core → Shop settings** nếu muốn kiểm tra tính phí.

## 4. Kiểm tra sau khi chạy

```powershell
docker compose exec web python manage.py check
docker compose run --rm web pytest -q
```

`pytest` dùng PostgreSQL test database riêng, không sửa database cửa hàng. Mở các địa chỉ:

| Địa chỉ | Kiểm tra |
| --- | --- |
| <http://localhost:8000/health/live/> | App đang chạy, HTTP 200 |
| <http://localhost:8000/health/ready/> | App kết nối PostgreSQL, HTTP 200 |
| <http://localhost:8000/> | Trang chủ |
| <http://localhost:8000/products/> | Sản phẩm và tìm kiếm |
| <http://localhost:8000/admin/> | Đăng nhập bằng superuser vừa tạo |
| <http://localhost:8000/orders/track/> | Theo dõi đơn gần nhất trong cùng phiên mua hoặc hướng dẫn tìm liên kết |

Trong Admin, tạo danh mục, sản phẩm, biến thể và ảnh tại **Catalog**. Điều chỉnh tồn tại **Inventory → Stocks → Adjust stock**; mỗi lần điều chỉnh có lịch sử. Thêm vào giỏ chưa trừ tồn. Đặt hàng COD thành công mới trừ tồn và tạo `Order` cùng `StockMovement`.

Để xử lý đơn, vào **Orders → Orders → Chuyển trạng thái**. Luồng hợp lệ là `PENDING → CONFIRMED → SHIPPING → COMPLETED`; có thể hủy khi `PENDING` hoặc `CONFIRMED`. Hủy hoàn tồn đúng một lần và ghi lịch sử trạng thái. Người mua xem trạng thái qua liên kết riêng được cấp sau checkout; ai có liên kết đều xem được đơn, nên cần giữ riêng. Khách không có danh sách lịch sử mua hoặc tài khoản.

## 5. Làm việc tiếp và cập nhật source

Trước khi bắt đầu công việc mới trên máy khác, mở repo trong VS Code/Codex và cho Codex đọc [file bàn giao](docs/HANDOFF_CODEX.md) cùng kế hoạch. Không tự triển khai Task 6 khi chưa có yêu cầu của chủ dự án.

Khi GitHub có commit mới, từ thư mục project chạy:

```powershell
git status --short
git pull --ff-only
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_roles
```

Nếu `git status --short` có thay đổi, kiểm tra trước khi pull để tránh ghi đè công việc đang làm. Trên repo này, nhánh hiện được đẩy lên GitHub là `task1-local`.

## 6. Dừng và xử lý lỗi thường gặp

```powershell
docker compose stop
docker compose start
docker compose logs --tail=100 db web
```

`docker compose stop/start` giữ nguyên dữ liệu. Có thể dùng `docker compose down` để gỡ container, nhưng **không thêm `-v`** nếu muốn giữ PostgreSQL và media volume. Công cụ backup/restore đầy đủ thuộc Task 6.

Nếu `docker compose up` báo không kết nối Docker, mở Docker Desktop và chờ Engine hoạt động. Nếu cổng 8000 đang bận, dừng chương trình chiếm cổng rồi chạy lại Compose. Nếu `/health/ready/` trả 503, kiểm tra `docker compose ps` và log `db`, `web`. Trang theo dõi đơn của một khách phải có URL token riêng dạng `/orders/track/<token>/`; `/orders/track/` chỉ mở đơn gần nhất khi còn cùng phiên trình duyệt.

## Truy vấn DB để đối chiếu

Các lệnh sau không in tên, điện thoại hoặc địa chỉ khách:

```powershell
docker compose exec db psql -U form -d form -c "SELECT display_number, status, subtotal, shipping_fee, total FROM orders_order ORDER BY id DESC LIMIT 5"
docker compose exec db psql -U form -d form -c "SELECT o.display_number, h.from_status, h.to_status, h.created_at FROM orders_orderstatushistory h JOIN orders_order o ON o.id=h.order_id ORDER BY h.id DESC LIMIT 10"
docker compose exec db psql -U form -d form -c "SELECT order_id, variant_id, delta, before, after FROM inventory_stockmovement WHERE order_id IS NOT NULL ORDER BY id DESC LIMIT 10"
```
