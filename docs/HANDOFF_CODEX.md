# FORM — bàn giao bối cảnh cho phiên Codex trên máy khác

Tài liệu này là bản tóm tắt có thể commit, **không phải bản chép toàn bộ cuộc trò chuyện**. Khi tiếp tục, đọc tài liệu này, [kế hoạch gốc](superpowers/plans/FORM_Project_Plan_v1.md), [README](../README.md), code và `git status` trước khi sửa. Kế hoạch gốc là đặc tả ban đầu; các checkbox trong đó chưa được cập nhật theo tiến độ thực tế.

## Quyết định của chủ dự án

- Một shop bán quần áo; v1 dùng **Django + templates/HTMX + PostgreSQL** và chạy **localhost bằng Docker Compose** trước. Máy ban đầu là Windows, RAM 16 GB, Docker đã cài.
- Khách mua **không đăng ký tài khoản**; thanh toán COD. Giỏ lưu trong session; thêm giỏ không giữ chỗ và không trừ tồn. Giá/tồn phải kiểm tra lại lúc đặt đơn.
- **Trừ tồn khi tạo đơn**. Hủy đơn hợp lệ hoàn tồn **đúng một lần**, có `StockMovement` và lịch sử chuyển trạng thái. Không mở rộng sang hosting nếu chủ dự án chưa yêu cầu.
- Giữ secret ngoài Git, không ghi đè thay đổi sẵn có. Kiểm tra môi trường và test trên PostgreSQL trước khi báo hoàn thành.

## Hiện trạng source

- Repository: `https://github.com/lqhuygt/agent-web-app.git`; nhánh đang dùng: `task1-local`. Dùng `git log -1 --oneline` để biết commit mới nhất. Docker Compose có `web`, `db`, volume `postgres_data`, `media_data`; web chỉ bind `127.0.0.1:8000`.
- **Task 1:** Django/PostgreSQL, cấu hình local, migration, health endpoints và Docker Compose.
- **Task 2:** `catalog` cho danh mục/sản phẩm/biến thể/ảnh; `inventory` cho tồn và lịch sử điều chỉnh; quản trị Django; `seed_demo`.
- **Task 3:** storefront, tìm kiếm tiếng Việt không dấu, lọc/phân trang, giỏ session và HTMX. Không trừ tồn khi thêm giỏ.
- **Task 4:** checkout COD khách vãng lai; `orders.services.place_order` dùng transaction, khóa stock, chống mua quá tồn và chống lặp theo session/idempotency key. Đơn lưu snapshot sản phẩm/giá. Người mua xem bằng token bí mật; DB chỉ lưu hash token.
- **Task 5:** `orders.services.transition_order` cho `PENDING → CONFIRMED → SHIPPING → COMPLETED` hoặc hủy từ `PENDING`/`CONFIRMED`. Hủy lặp và hủy đồng thời không hoàn tồn thêm; `OrderStatusHistory` lưu actor/thời gian/lý do. Admin không cho sửa trực tiếp status, giá, tổng tiền hoặc stock. `setup_roles` tạo ba nhóm quyền. `core.rate_limit` lưu bộ đếm login/checkout trong DB. Trang `/orders/track/` mở đơn gần nhất khi còn cùng phiên mua; khi mất phiên chỉ hướng dẫn dùng liên kết đã lưu.
- Các test hiện có nằm trong `tests/`, gồm checkout cạnh tranh, hủy cạnh tranh, quyền staff và truy cập đơn. Lần kiểm tra gần nhất trước bản bàn giao này: **72 test đạt trên PostgreSQL test database**. Cần chạy lại trên máy mới; đừng xem kết quả cũ là bằng chứng môi trường mới đã đạt.

## Mốc làm việc với chủ dự án

- Chủ dự án đã trực tiếp thử tạo user, quản trị catalog/kho, giỏ hàng, đặt đơn và kiểm tra đơn/tồn trong DB. Quy tắc trừ tồn **khi đặt đơn** đã được chủ dự án nhắc lại và xác nhận.
- Chủ dự án đã chuyển một đơn sang `SHIPPING` và kiểm tra lịch sử trạng thái. Sau đó đã yêu cầu sửa `/orders/track/` để không còn 404 và sửa dòng trạng thái cố định trên trang theo dõi; các sửa đổi này đã ở Git.
- Chủ dự án muốn làm tiếp trên máy khác **chỉ với source**, không chuyển database, ảnh, user hoặc `.env` của máy cũ. Máy mới sẽ bắt đầu với DB trống và cần tạo superuser mới.
- **Task 6 chưa được bàn giao.** Ngày 20/11/2026 đã có một lượt thử Task 6 tạm thời, nhưng chủ dự án yêu cầu xóa toàn bộ mã kiểm thử, Compose test, script và tài liệu của lượt thử đó trước khi bàn giao Git. Nhánh này chỉ chứa Task 1–5; không coi kiểm thử tải, browser E2E, backup/restore hoặc CI của Task 6 là đã có trong source. Chỉ tiếp tục Task 6 khi chủ dự án yêu cầu; hosting vẫn ngoài phạm vi hiện tại.

## Điểm bắt đầu cho Codex phiên mới

1. Xác nhận đúng repository/nhánh, `git status`, `AGENTS.md` nếu có và môi trường thực tế của máy mới. Đọc README để dựng `.env` và Docker.
2. Đọc kế hoạch Task 6 trước khi đề xuất hoặc triển khai; đối chiếu code hiện tại với kế hoạch, không dựa vào checkbox chưa cập nhật.
3. Dùng PostgreSQL test database riêng khi chạy `docker compose run --rm web pytest -q`. Không dùng DB cửa hàng để thử nghiệm có thể đổi dữ liệu.
4. Hỏi chủ dự án về yêu cầu tiếp theo nếu họ chưa giao Task 6; dừng ở phạm vi được giao.

Có thể mở chat mới trong thư mục repo và gửi: “Đọc `docs/HANDOFF_CODEX.md`, `README.md` và kế hoạch FORM. Task 1–5 đã làm trên nhánh `task1-local`. Hãy kiểm tra môi trường máy này, trạng thái Git và hỏi tôi trước khi bắt đầu Task 6.”
