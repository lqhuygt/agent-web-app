# FORM v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline implementation, or superpowers:subagent-driven-development only if that execution method is selected. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây cửa hàng quần nam chạy localhost theo phạm vi chủ dự án đã duyệt.

**Architecture:** Một ứng dụng Django chia module catalog, inventory, cart, orders và core. PostgreSQL giữ dữ liệu nghiệp vụ; giỏ dùng database-backed session. App và database chạy dịch vụ Compose riêng.

**Tech Stack:** Python 3.13, Django 5.2 LTS, HTMX, PostgreSQL 17, Docker Compose; pytest/pytest-django, Playwright và k6 cho kiểm thử. Chọn và khóa bản vá tương thích khi bắt đầu thực hiện.

**Spec:** Phần “Phạm vi đã duyệt” ngay trong tài liệu này (mục 1–9), giữ cùng kế hoạch. Khi đặt vào repository, lưu tài liệu tại `docs/superpowers/plans/2026-11-19-form-v1.md`.

## Global Constraints

- Một cửa hàng bán quần nam; giao diện dựa trên mẫu FORM đã duyệt.
- Không đăng ký/đăng nhập tài khoản khách; quản trị bắt buộc xác thực và phân quyền.
- Trừ tồn khi tạo đơn; hủy hoàn một lần; lịch sử điều chỉnh.
- COD; phí ship cố định và ngưỡng miễn phí cấu hình được.
- PostgreSQL cả local và test; không thay bằng SQLite khi kiểm tra transaction/concurrency.
- Localhost trước; không mua dịch vụ hay triển khai hosting ở giai đoạn này.
- Mục tiêu tải và bàn giao theo mục 6 và 8; chưa được coi là đã đạt trước khi thực chạy.

## Review Focus

- Hai session mua chiếc cuối: chỉ một đơn thành công; test task 4.
- Gửi checkout lặp hoặc cùng khóa nhưng đổi nội dung: không tạo đơn/trừ tồn thêm; test task 4.
- Thao tác quản trị bỏ qua quy tắc hoặc hủy lặp: server từ chối, không hoàn tồn lặp; test task 5.
- Khởi động lại, backup/restore: dữ liệu và ảnh vẫn dùng được; kiểm tra task 6.
- Khách lấy đường dẫn đơn khác hoặc nội dung nhập chứa HTML: không lộ dữ liệu qua mã đoán được, không thực thi nội dung; test task 4 và 6.

---

## Phạm vi đã duyệt

Ngày lập: 18/11/2026; cập nhật chốt phạm vi: 19/11/2026  
Trạng thái: Chủ dự án đã duyệt phương án A và phạm vi v1 ngày 19/11/2026. Thực hiện local trước; hosting cần yêu cầu riêng sau nghiệm thu.  
Chủ dự án: Huy GT  
Sản phẩm: Website bán quần nam của một cửa hàng.

## 1. Mục tiêu và những gì đã thống nhất

- Một cửa hàng tự bán sản phẩm; không có người bán bên thứ ba.
- Lấy giao diện FORM đã xem và thử làm mẫu về phong cách và trải nghiệm.
- Tạo project có mã nguồn, backend, database, quản trị, tài liệu chạy và kiểm thử.
- Chạy trên localhost của chủ dự án trước; chỉ triển khai hosting khi chủ dự án yêu cầu sau khi nghiệm thu.
- Thiết kế và kiểm thử theo mục tiêu khoảng 100 người dùng đồng thời; chưa cam kết công suất trước khi có kết quả đo.
- Người mua sử dụng website độc lập, không cần tài khoản ChatGPT.

## 2. Các phương án đã cân nhắc — đã chọn A

| Phương án | Thành phần | Điểm mạnh | Đánh đổi |
| --- | --- | --- | --- |
| A — đã chọn | Django + Templates/HTMX + PostgreSQL | Tận dụng Python/SQL của chủ dự án; một ứng dụng; có nền tảng quản trị nội bộ | Giao diện tương tác phức tạp cần thêm JavaScript; mobile sau này cần API |
| B | Next.js full-stack + PostgreSQL | React/TypeScript cho cả giao diện và logic phía server; thuận tiện phát triển giao diện | Chủ dự án cần làm quen TypeScript; phải xây hoặc tích hợp phần quản trị |
| C | React/Next.js + Django/FastAPI API riêng + PostgreSQL | Backend có thể dùng chung cho web/mobile; phát triển độc lập | Thêm ranh giới API, xác thực, kiểm thử tích hợp và thành phần triển khai |

Quyết định của chủ dự án: A — Django + Templates/HTMX + PostgreSQL. Giữ B/C để ghi lại các phương án đã cân nhắc. Mục tiêu 100 người đồng thời không tự tạo ra yêu cầu tách frontend/backend.

Cấu hình đã chốt theo A:

- Python 3.13; Django 5.2 LTS và bản vá tương thích được kiểm tra tại thời điểm khởi tạo.
- PostgreSQL 17 với bản vá phù hợp; dùng PostgreSQL cả local và khi kiểm thử.
- Templates + HTMX + CSS/JavaScript; chuyển phong cách demo sang giao diện lấy dữ liệu từ server.
- Django Admin cho quản trị nội bộ; màn hình riêng cho thao tác đơn hàng nếu quản trị mặc định không phù hợp.
- Docker Compose là cách chạy chuẩn: app và database là dịch vụ riêng; thay đổi mã nguồn có thể tự tải lại trong môi trường phát triển.
- Database và ảnh có volume bền vững. Cấu hình ví dụ không chứa mật khẩu thật; dependency và image được khóa phiên bản có thể tái tạo.
- Git lưu thay đổi; lựa chọn GitHub/GitLab sau khi xác định nơi lưu repository.
- Bộ kiểm thử dự kiến: pytest/pytest-django, Playwright và k6. Phiên bản công cụ được xác minh khi lập kế hoạch code chi tiết.

## 3. Phạm vi nghiệp vụ v1 — đã duyệt

### Khách mua hàng

- Trang chủ, danh mục, danh sách và chi tiết sản phẩm; dùng tốt trên desktop và điện thoại.
- Tìm kiếm tên sản phẩm có dấu/không dấu, không phân biệt hoa thường; xử lý khoảng trắng thừa.
- Lọc danh mục, giá; sắp xếp giá; phân trang.
- Ảnh sản phẩm, mô tả, bảng size; chọn màu, size và số lượng; hiển thị khả năng mua theo tồn kho.
- Giỏ hàng lưu bằng session phía server; thêm, sửa số lượng, xóa. Giá và tồn được kiểm tra lại khi đặt đơn.
- Đặt hàng không bắt buộc tạo tài khoản: tên, điện thoại, địa chỉ, ghi chú; thanh toán COD.
- Xác nhận đơn và trang xem đơn qua mã truy cập ngẫu nhiên, khó đoán; mã đơn tuần tự/điện thoại không đủ để xem thông tin đơn.
- Không xây đăng ký/đăng nhập tài khoản khách trong v1. Khách mua không cần tài khoản; quản trị vẫn phải đăng nhập.

### Chủ shop và nhân viên được phân quyền

- Đăng nhập quản trị; chủ shop được cấp quyền cần thiết, không cung cấp đăng ký quản trị công khai.
- Quản lý danh mục, sản phẩm, mô tả, ảnh, giá, trạng thái bán/ẩn.
- Quản lý mã SKU và tồn theo từng tổ hợp sản phẩm–màu–size.
- Điều chỉnh tồn có lý do và lịch sử; danh sách sản phẩm sắp hết hàng với ngưỡng cấu hình.
- Xem, tìm và lọc đơn; xem thông tin người mua; cập nhật trạng thái theo luồng được phép.
- Phân quyền quản lý sản phẩm, kho và đơn hàng. Thao tác nhạy cảm kiểm tra quyền tại server.
- Cấu hình phí giao hàng cố định và ngưỡng miễn phí trong v1. Các mức giá demo chỉ là dữ liệu mẫu, chưa là chính sách thật.

### Quy tắc đơn và tồn kho

- Luồng đã chốt: Chờ xác nhận → Đã xác nhận → Đang giao → Hoàn tất.
- Hủy được khi Chờ xác nhận hoặc Đã xác nhận. Đơn Đang giao/Hoàn tất không dùng thao tác hủy để hoàn kho; trả hàng và hoàn tiền chưa nằm trong v1.
- Trừ tồn ngay khi tạo đơn thành công; đơn COD do chủ shop xác nhận thủ công.
- Đơn hủy hoàn tồn đúng một lần. Chuyển trạng thái và hoàn tồn có kiểm tra để tránh thực hiện lặp.
- Tạo đơn, lưu chi tiết và cập nhật tồn trong cùng một transaction; kiểm soát mua đồng thời bằng khóa/cập nhật có điều kiện tại database.
- Giá tiền và tổng thanh toán do server tính; sử dụng kiểu số tiền chính xác. Lưu ảnh chụp tên/SKU/giá của dòng hàng và phí ship trong đơn.
- Có cơ chế chống tạo đơn trùng khi gửi lại cùng yêu cầu. Lỗi giữa chừng phải rollback toàn bộ thay đổi.
- Nghiệp vụ đơn và kho dùng chung cho các đường vào, gồm cả thao tác quản trị; không cho sửa trực tiếp trạng thái để bỏ qua kiểm soát.

## 4. Phần chưa làm trong v1

- Marketplace nhiều người bán; ứng dụng mobile; chat thời gian thực; gợi ý sản phẩm bằng AI.
- Thanh toán qua cổng, đối soát/hoàn tiền tự động.
- Kết nối hãng vận chuyển, tính phí theo vùng và in vận đơn tự động.
- Voucher, tích điểm, affiliate, đánh giá công khai và chiến dịch flash sale.
- Quy trình trả hàng/đổi size trực tuyến tự động; đồng bộ kho giữa nhiều kênh bán.
- Dashboard BI nâng cao, microservices, Kubernetes, hàng đợi nền hoặc cache phân tán khi chưa có nhu cầu đã đo.

Các phần này có thể thêm sau; nếu cần cho ngày mở bán phải đổi phạm vi trước khi code.

## 5. Các giai đoạn và điều kiện hoàn thành

| Giai đoạn | Công việc | Kết quả để kiểm tra |
| --- | --- | --- |
| 0. Chốt thiết kế | Chọn stack, xác nhận phạm vi v1, quy tắc kho/đơn, máy local; hoàn thiện thiết kế và kế hoạch code | Tài liệu thiết kế được chủ dự án duyệt; sau đó mới khởi tạo/code |
| 1. Nền tảng | Repository, cấu hình local, Compose, database, migrations, seed data, tài khoản quản trị qua bước thiết lập | Khởi động theo README; kiểm tra health; khởi động lại không mất dữ liệu |
| 2. Sản phẩm và kho | Mô hình danh mục/sản phẩm/SKU/ảnh; quản trị; điều chỉnh tồn có lịch sử | Tạo quần mới có nhiều màu–size, nhập tồn và xem được ngoài cửa hàng |
| 3. Luồng mua | Giao diện, tìm kiếm/lọc/phân trang, chi tiết, giỏ hàng, checkout COD và xác nhận đơn | Mua từ đầu đến cuối bằng dữ liệu database; xử lý hết hàng/nhập sai/thay đổi giá |
| 4. Vận hành đơn | Danh sách đơn, phân quyền, trạng thái, hoàn tồn khi hủy, lịch sử thao tác | Chủ shop xử lý được vòng đời đơn; người không có quyền bị từ chối |
| 5. Kiểm thử và sửa lỗi | Nghiệp vụ, tích hợp PostgreSQL, trình duyệt, bảo mật liên quan và kiểm thử tải | Bộ kiểm thử đạt; báo cáo tải có cấu hình, dữ liệu, kịch bản và số liệu; lỗi còn lại được ghi rõ |
| 6. Bàn giao local | README, lệnh vận hành, hướng dẫn nhập dữ liệu/sao lưu/khôi phục, checklist UAT | Chủ dự án tự chạy và thử theo checklist trên máy của mình |
| 7. Hosting — chưa thực hiện | Chọn hạ tầng, tên miền, HTTPS, cấu hình production, sao lưu ngoài máy, giám sát và quy trình phát hành | Chỉ bắt đầu theo yêu cầu tiếp theo; kiểm thử lại trên hạ tầng thực |

Mỗi giai đoạn có bản chạy hoặc bằng chứng kiểm tra cụ thể. Chưa chốt thời gian/cost khi chưa xác nhận máy chạy và phạm vi triển khai chi tiết; không dùng ước lượng như cam kết ngày giao.

## 6. Kiểm thử và tiêu chí nghiệm thu

### Chức năng và tính đúng đắn

- Tìm kiếm từ khóa có/không dấu, chữ hoa, khoảng trắng, từ không có kết quả và xóa từ khóa.
- Các bộ lọc kết hợp đúng; thao tác trên mobile không mất giỏ hoặc che nút đặt đơn.
- Người mua không xem/sửa đơn của người khác; khách không truy cập được quản trị.
- Server không tin giá/tổng tiền/số tồn do trình duyệt gửi lên.
- Với tồn ban đầu là 1 và nhiều yêu cầu hợp lệ đồng thời: tối đa 1 đơn được tạo thành công cho SKU đó, không âm tồn, các yêu cầu còn lại nhận thông báo hết hàng.
- Gửi lặp cùng yêu cầu checkout không tạo đơn thứ hai; test cả trường hợp đồng thời.
- Hủy đơn nhiều lần không hoàn tồn nhiều lần; rollback khi tạo đơn thất bại.
- Đơn cũ giữ đúng giá và thông tin dòng hàng khi sản phẩm được đổi giá/ẩn.
- Database và ảnh còn nguyên khi restart container; sao lưu và khôi phục được thử với dữ liệu mẫu.

### Mục tiêu hiệu năng — cần đo, chưa phải bảo đảm

- Chuẩn bị dữ liệu thử có danh mục, ảnh và biến thể đủ đại diện; quy mô cụ thể được ghi trong thiết kế chi tiết.
- k6 tăng dần 10 → 50 → 100 người dùng mô phỏng; giữ 100 người trong 15 phút, có thời gian đọc và thao tác giữa các yêu cầu.
- Kịch bản gồm xem danh sách, tìm kiếm/lọc, xem chi tiết, giỏ và đặt đơn với session độc lập.
- Mục tiêu p95 phía server: dưới 500 ms cho danh sách/tìm kiếm, dưới 1 giây cho tạo đơn; lỗi server dưới 1%. Ghi riêng hết hàng dự kiến và lỗi hệ thống.
- Đo throughput/RPS, p95, CPU/RAM, kết nối và thời gian truy vấn database. Đo trải nghiệm trình duyệt/ảnh riêng; k6 HTTP không thay thế kiểm thử hiển thị.
- Ghi rõ phần cứng và vị trí máy phát tải. Kết quả local chỉ có giá trị với cấu hình đã đo; nghiệm thu tải cuối cùng cần môi trường tương đương production và máy phát tải riêng.
- Không đánh đổi đúng đắn đơn/tồn để đạt tốc độ. Nếu chưa đạt, phân tích số liệu và sửa trước khi kết luận.

## 7. Chuẩn bị từ chủ dự án

Cần biết trước bước khởi tạo:

1. Hệ điều hành và cấu hình máy local; Docker/WSL đã cài hay chưa; có bị hạn chế quyền cài đặt hoặc mạng không.
Phương án A và việc không xây tài khoản khách đã được chốt; không hỏi lại các quyết định này.

Có thể dùng dữ liệu mẫu để phát triển; cần dữ liệu thật trước khi mở bán:

- Tên thương hiệu (FORM hiện là tên tạm), logo và thông tin liên hệ.
- Danh mục, tên, mô tả, ảnh có quyền sử dụng, size/màu, SKU, giá và tồn thực tế.
- Chính sách giao hàng, đổi/trả, bảo mật; phí ship và ngưỡng miễn phí.
- Nơi lưu Git repository, tên miền và hosting khi đến giai đoạn triển khai.

## 8. Bộ bàn giao dự kiến

- Mã nguồn quản lý bằng Git, chia module; migrations và dữ liệu mẫu không có dữ liệu cá nhân thật.
- Dockerfile/Compose, file cấu hình mẫu, dependency được khóa và tài liệu phiên bản.
- Thiết kế dữ liệu, mô tả luồng đơn/tồn và các quyết định kỹ thuật.
- Kiểm thử tự động, kịch bản tải và báo cáo kết quả thực chạy; không trình bày mục tiêu thành số liệu đã đạt.
- README khởi động, tạo quản trị, nhập dữ liệu, chạy test, sao lưu/khôi phục và xử lý lỗi thường gặp.
- Checklist người dùng tự nghiệm thu; danh sách hạn chế và việc cần làm trước hosting.

## 9. Các quyết định đã chốt

| Quyết định | Quyết định | Trạng thái |
| --- | --- | --- |
| Công nghệ | A: Django + HTMX + PostgreSQL | Đã chốt 19/11/2026 |
| Môi trường | Docker Compose; localhost trước | Đã chốt 19/11/2026 |
| Bán hàng | Một shop, COD, ship cấu hình đơn giản | Đã chốt 19/11/2026 |
| Tài khoản khách | Checkout không đăng ký, xem đơn bằng mã truy cập bảo mật | Đã chốt 19/11/2026 |
| Kho | Trừ tồn khi tạo đơn; hủy hoàn một lần; lịch sử điều chỉnh | Đã chốt 19/11/2026 |
| Giao diện | Phong cách demo FORM, thay dữ liệu tĩnh bằng dữ liệu server | Demo đã được chấp nhận làm mẫu |
| Hiệu năng | Mục tiêu 100 người đồng thời, kiểm chứng bằng tải thực tế | Đã chốt mục tiêu và tiêu chí; cần đo khi thực hiện |
| Hosting | Chuẩn bị đường triển khai, chưa mua/chưa phát hành | Chỉ thực hiện theo yêu cầu sau nghiệm thu local |

Triển khai theo kế hoạch bên dưới sau khi xác định môi trường local. Các lựa chọn về công nghệ, tài khoản khách và kho đã được duyệt; không mở lại trừ khi chủ dự án yêu cầu.

## 10. Kế hoạch triển khai theo nhiệm vụ

Chưa có bước nào dưới đây được thực hiện. Đường dẫn tính từ repository gốc; các package có `__init__.py`, `apps.py` và migrations khi có model. Lần đầu khởi tạo chuẩn bị `pytest.ini`, `tests/conftest.py`, `manage.py` và `requirements/` trong task 1. Mọi test dùng database PostgreSQL test riêng, không chạy trên dữ liệu chủ shop.

### Task 1 — Nền tảng local có dữ liệu bền vững

**Files:** `Dockerfile`, `compose.yaml`, `.env.example`, `.gitignore`, `requirements/base.in`, `requirements/dev.in`, các file lock tương ứng, `manage.py`, `config/settings/{base,local,production}.py`, `config/urls.py`, `core/views.py`, `tests/test_health.py`, `README.md`.

**Interfaces:** `GET /health/live/` trả HTTP 200 khi app chạy; `GET /health/ready/` kiểm tra database bằng truy vấn nhẹ, trả 200 khi kết nối được và 503 khi không; không lộ thông tin kết nối. Compose có dịch vụ `web`, `db`, volume `postgres_data`, `media_data`; local chỉ publish các cổng cần thiết trên loopback.

- [ ] Xác nhận hệ điều hành máy đích và Docker; chọn/khóa dependency tương thích; chuẩn bị môi trường Git riêng. Không ghi secret hoặc thư mục dữ liệu vào Git.
- [ ] Viết `test_live_returns_200` và `test_ready_requires_database`. Assertion điển hình: `assert client.get('/health/ready/').status_code == 200` trên PostgreSQL có kết nối.
- [ ] Chạy `docker compose run --rm web pytest tests/test_health.py -q` sau khi môi trường tối thiểu sẵn sàng; xác nhận test thất bại vì endpoint chưa được triển khai, không phải vì thiếu dependency.
- [ ] Tạo project Django, cấu hình session trong database, timezone `Asia/Ho_Chi_Minh`, môi trường riêng và health endpoints. Local dùng cơ chế tải lại code; cấu hình production không dùng development server.
- [ ] Chạy `docker compose up -d --build`, migrate và các health test; kiểm tra readiness trả 503 khi database dừng trong môi trường thử.
- [ ] Kiểm tra một bản ghi và file ảnh thử còn tồn tại sau restart; ghi hướng dẫn không dùng thao tác xóa volume để khởi động thường ngày. Commit `chore: bootstrap local Django and PostgreSQL`.

### Task 2 — Catalog, biến thể, kho và quản trị sản phẩm

**Files:** `catalog/{models,admin,forms}.py`, `inventory/{models,services,admin,forms}.py`, `core/models.py`, migrations, `catalog/management/commands/seed_demo.py`, `tests/{test_catalog_models,test_inventory,test_catalog_admin,test_seed}.py`.

**Interfaces:**

- `Category`: name, slug, active. `Product`: category, name, slug, description, price, active, size_guide; `ProductImage`: product, image, alt_text, position.
- `ProductVariant`: product, color, size, unique sku, active; unique tổ hợp product–color–size.
- `Stock`: one-to-one variant, quantity không âm, low_stock_threshold không âm.
- `StockMovement`: variant, delta, before, after, reason, actor, order (nullable), created_at; lịch sử không chỉnh/sửa/xóa bằng màn hình quản trị.
- `adjust_stock(*, variant_id: int, delta: int, reason: str, actor: User) -> StockMovement`: kiểm tra quyền `inventory.adjust_stock`, lý do bắt buộc, khóa dòng và không cho kết quả âm.
- `ShopSettings`: một cấu hình tiền VND chính xác gồm flat_shipping_fee, free_shipping_threshold; đều không âm. Phép tính tiền dùng Decimal, v1 không hỗ trợ nhiều tiền tệ.

- [ ] Viết test: SKU/tổ hợp biến thể không trùng; không lưu giá/tồn âm; nhập tồn +5 tạo lịch sử 0→5; điều chỉnh -6 khi tồn 5 bị từ chối, không tạo lịch sử; người thiếu quyền không điều chỉnh được. Ví dụ: `assert movement.after == 5; assert movement.delta == 5`.
- [ ] Chạy `docker compose run --rm web pytest tests/test_catalog_models.py tests/test_inventory.py tests/test_catalog_admin.py tests/test_seed.py -q`; xem các failure vì model/service chưa có.
- [ ] Triển khai model, constraint, dịch vụ điều chỉnh và màn hình quản trị có form riêng. Không expose trường quantity cho sửa trực tiếp; ảnh upload chỉ nhận định dạng raster cho phép, kiểm tra nội dung và giới hạn 5 MiB/file; không nhận SVG trong v1. Dùng Pillow xác minh ảnh.
- [ ] Viết và kiểm tra `seed_demo`: tạo dữ liệu giả có nhận diện cố định, chạy lại không nhân bản và không ghi đè giá/tồn đã được chủ shop sửa. Seed không tạo mật khẩu quản trị mặc định.
- [ ] Chạy migrations và toàn bộ test hiện có; tạo dữ liệu mẫu bằng `docker compose exec web python manage.py seed_demo`; kiểm tra thêm quần với hai size và hai màu. Commit `feat: catalog and audited inventory management`.

### Task 3 — Giao diện, tìm kiếm và giỏ session

**Files:** `catalog/{views,urls,queries}.py`, `cart/{services,views,urls,forms}.py`, `templates/{base,storefront,products,cart}/`, `static/{css,js}/`, `tests/{test_search,test_catalog_views,test_cart}.py`.

**Interfaces:**

- `GET /`, `GET /products/`, `GET /products/<slug>/`.
- `search_products(*, q: str, category_slug: str | None, min_price: Decimal | None, max_price: Decimal | None, sort: str) -> QuerySet[Product]`. Chuẩn hóa dấu/chữ hoa/khoảng trắng; chỉ trả sản phẩm active trong danh mục active. Dùng trường tìm kiếm chuẩn hóa được đồng bộ khi sửa tên; sort chỉ nhận danh sách cho phép.
- Danh sách tối đa 24 sản phẩm/trang, query parameters được giữ khi chuyển trang. Price filter sai định dạng nhận thông báo rõ, không gây HTTP 500.
- `GET /cart/`, POST thêm/đổi/xóa variant; `set_cart_quantity(*, request: HttpRequest, variant_id: int, quantity: int) -> None`. Session lưu variant id và số lượng, không tin giá từ client; quantity 0 là xóa, quantity âm hoặc không nguyên bị từ chối. Tối đa 10 đơn vị/biến thể mỗi đơn là giới hạn kỹ thuật ban đầu, hiển thị rõ.

- [ ] Viết test literal cho `quan au`, `QUẦN ÂU`, `  quần   âu  ` trả đúng sản phẩm; lọc kết hợp và phân trang giữ q; ẩn sản phẩm không còn xuất hiện; session A/B có giỏ độc lập; giỏ cập nhật tổng sau đổi giá; thêm vượt tồn/quantity không hợp lệ bị từ chối.
- [ ] Chạy `docker compose run --rm web pytest tests/test_search.py tests/test_catalog_views.py tests/test_cart.py -q`; xác nhận failures tương ứng.
- [ ] Triển khai queries, routes, template FORM và session cart; dùng HTMX cho cập nhật vùng giao diện. Form vẫn hoạt động khi không có HTMX; mọi POST có CSRF. Chọn màu/size biểu diễn bằng variant cụ thể; variant ẩn/hết hàng có thông báo.
- [ ] Chạy toàn bộ test; kiểm tra keyboard focus, thông báo lỗi, desktop và viewport 390 px bằng browser. Commit `feat: storefront search and session cart`.

### Task 4 — Checkout COD có transaction và chống lặp

**Files:** `orders/{models,forms,services,views,urls,exceptions}.py`, migrations, `templates/checkout/`, `templates/orders/`, `tests/{test_checkout,test_order_access,test_checkout_concurrency}.py`.

**Interfaces:**

- `CheckoutInput`: name, phone, address, note. Validate độ dài/tên/điện thoại/địa chỉ ở server; không đặt giới hạn trình duyệt làm nguồn kiểm tra duy nhất.
- `OrderStatus`: PENDING, CONFIRMED, SHIPPING, COMPLETED, CANCELLED. `Order`: mã hiển thị, trạng thái, thông tin giao hàng, subtotal/shipping_fee/total, created_at; `OrderItem`: variant, quantity, snapshot_name/sku/color/size/unit_price/line_total. Không xóa đơn cũ khi ẩn sản phẩm.
- `CheckoutAttempt`: session_key + idempotency UUID unique theo session, fingerprint payload và tham chiếu order. `place_order(*, session_key: str, idempotency_key: UUID, customer: CheckoutInput, lines: list[CartLine]) -> Order`, `CartLine(variant_id: int, quantity: int)`.
- Lần gửi lại cùng khóa/nội dung trả order cũ; cùng khóa nhưng nội dung khác trả lỗi conflict, không thay order đã tạo. Các khóa khác nhau vẫn kiểm tra tồn trong transaction.
- `GET /checkout/`, `POST /checkout/`; khi thành công redirect trang xác nhận và xóa giỏ sau commit. Lưu khóa checkout trên session để tải lại không tạo khóa mới cho yêu cầu đang gửi.
- `GET /orders/track/<token>/`: token ngẫu nhiên tối thiểu 256 bit, database chỉ lưu hash token; URL không có điện thoại/địa chỉ. Token sai trả 404. Đặt `Referrer-Policy: no-referrer`, không nhúng tài nguyên bên thứ ba ở trang đơn; log che token và dữ liệu giao hàng. Ai có liên kết có thể xem đơn, giao diện giải thích không chia sẻ liên kết.

- [ ] Viết test: đơn giá 449.000 × 1 + ship 30.000 = 479.000; đạt ngưỡng 699.000 thì ship 0; chỉnh giá client không ảnh hưởng; snapshot không đổi khi sản phẩm đổi giá; lỗi lưu dòng hàng rollback order/stock/history; token sai không xem được đơn; nội dung `<script>` bị escape.
- [ ] Viết transaction tests với kết nối PostgreSQL riêng và điểm đồng bộ, không dựa vào sleep: tồn 1, hai session/khóa khác nhau mua cùng lúc → đúng 1 order, tồn 0; cùng session/khóa gửi đồng thời → đúng 1 order và đúng 1 lần trừ. Thêm test khóa cũ với payload khác bị conflict.
- [ ] Chạy `docker compose run --rm web pytest tests/test_checkout.py tests/test_order_access.py tests/test_checkout_concurrency.py -q`; quan sát failure trước triển khai.
- [ ] Triển khai bằng transaction atomic; khóa CheckoutAttempt để tuần tự hóa cùng yêu cầu, khóa variant/stock theo variant_id tăng dần để giảm deadlock; kiểm tra active/giá/tồn sau khi khóa. Không gửi giá hoặc token bí mật trong log. Tất cả đường ghi đơn đều gọi service này.
- [ ] Chạy toàn bộ test và mua thử qua trình duyệt không đăng nhập. Commit `feat: transactional guest COD checkout`.

### Task 5 — Xử lý đơn, phân quyền và hủy hoàn tồn một lần

**Files:** `orders/{services,admin,forms}.py`, `inventory/services.py`, `core/management/commands/setup_roles.py`, `tests/{test_order_transitions,test_cancellation_concurrency,test_staff_permissions}.py`.

**Interfaces:** `transition_order(*, order_id: int, target_status: OrderStatus, actor: User, reason: str = '') -> Order`. PENDING→CONFIRMED→SHIPPING→COMPLETED; PENDING/CONFIRMED→CANCELLED; hủy lại CANCELLED là no-op không thêm movement. Bước chuyển ngược hoặc hủy SHIPPING/COMPLETED bị từ chối.

- [ ] Viết test cho từng chuyển hợp lệ/bất hợp lệ; hủy 2 lần và hủy đồng thời chỉ hoàn một lần; người thiếu quyền nhận 403; SKU gần hết hiển thị theo ngưỡng. Ví dụ với quantity đặt 2: `assert stock.quantity == original_quantity` sau hủy lặp, chỉ 1 movement hoàn của SKU trong đơn.
- [ ] Chạy `docker compose run --rm web pytest tests/test_order_transitions.py tests/test_cancellation_concurrency.py tests/test_staff_permissions.py -q`; xác nhận thất bại vì hành vi chưa có.
- [ ] Triển khai service khóa order trước, stock theo cùng thứ tự task 4; hoàn tồn và trạng thái trong một transaction. Lịch sử trạng thái lưu actor/thời gian/lý do. Trường trạng thái, giá snapshot, tổng tiền và stock readonly trong admin; thao tác chuyển trạng thái gọi service, không dùng bulk update trực tiếp.
- [ ] Tạo quyền theo vai trò quản lý sản phẩm/kho/đơn; admin session dùng Django auth. Bổ sung giới hạn lần thử đăng nhập và checkout cấu hình được, lưu bộ đếm dùng chung ở database trong v1; không dựa vào bộ nhớ riêng từng worker.
- [ ] Chạy toàn bộ test và thử các nhóm quyền qua trình duyệt. Commit `feat: order operations and staff permissions`.

### Task 6 — Nghiệm thu, tải và bàn giao có thể tái tạo

**Files:** `tests/e2e/test_storefront.py`, `tests/test_security.py`, `tests/test_query_budget.py`, `tests/load/form.js`, `compose.test.yaml`, `scripts/{backup,restore}.sh`, `docs/{uat,operations,load-report}.md`, `README.md`, cấu hình CI phù hợp repository được chọn.

**Interfaces:** Các lệnh chuẩn: `docker compose up -d --build`, `docker compose exec web python manage.py migrate`, `docker compose exec web python manage.py createsuperuser`, `docker compose run --rm web pytest`. README giải thích bước tạo `.env`, seed, backup/restore và lệnh chạy E2E/load; khởi động local không cần secret hosting.

- [ ] Trước khi sửa các lỗi nghiệm thu, thêm test tái hiện: POST thiếu CSRF bị chặn; người không có quyền bị chặn; ảnh không hợp lệ bị từ chối; lỗi không lộ secret. E2E dùng session mới thực hiện tìm `quan au`, chọn size, thêm giỏ và COD; kiểm tra order trong PostgreSQL có đúng 1 bản ghi. Chạy test để quan sát lỗi cụ thể trước mỗi bản sửa.
- [ ] Chạy toàn bộ `pytest` trên PostgreSQL và E2E trên môi trường browser được hỗ trợ; không thay thế một lỗi browser bằng khẳng định test đã đạt. Đếm truy vấn danh sách để phát hiện N+1 khi tăng số sản phẩm trong một trang.
- [ ] Chuẩn bị fixture tải riêng 500 sản phẩm × 6 biến thể, tồn đủ cho tải, không có thông tin cá nhân thật; khóa việc chạy tải trên database vận hành. `k6` dùng cookie jar/session và dữ liệu checkout riêng từng VU, giữ CSRF, xử lý redirect và assert response thực; không chỉ đo HTTP 200.
- [ ] Chạy ramp 10→50→100 VU và giữ 100 trong 15 phút; giữ mục tiêu mục 6, ghi số yêu cầu/RPS/p95/lỗi, CPU/RAM/database và cấu hình app/DB. Dùng Gunicorn cho bài tải, không development server. Nếu hạ tầng hiện tại không hỗ trợ chạy tải/E2E, ghi chưa kiểm chứng và bàn giao lệnh chạy; không báo đạt.
- [ ] Thử backup database + media, restore sang volume/database test mới rồi đối chiếu SKU/tồn/đơn/ảnh; không ghi đè dữ liệu đang dùng. Tài liệu có hướng dẫn Linux shell qua WSL nếu máy chủ dự án dùng Windows.
- [ ] Chạy `python manage.py check --deploy --settings=config.settings.production` với cấu hình production thử, khắc phục các lỗi cần thiết; không công khai server/không triển khai hosting. Mọi cấu hình đặc thù hosting vẫn ghi là công việc giai đoạn sau.
- [ ] Đóng gói source, hướng dẫn, test, báo cáo đã chạy và danh sách chưa kiểm chứng; loại `.env`, volume, secret, dữ liệu người thật. Commit `test: verify local storefront and document operations`.

## 11. Tự rà soát kế hoạch

- Phạm vi đã duyệt ánh xạ vào task 1–6; hosting nằm ngoài phần thực hiện.
- Interface `CartLine`, `CheckoutInput`, `place_order`, `adjust_stock`, `transition_order` được dùng thống nhất.
- Transaction, idempotency, truy cập đơn, quản trị và backup có kiểm tra cụ thể.
- Chưa chạy test sản phẩm vì chưa viết mã sản phẩm; các lệnh ở trên là bước sẽ thực hiện, không phải bằng chứng đã đạt.
- Thông tin còn thiếu để tùy chỉnh hướng dẫn chạy: hệ điều hành máy local, CPU/RAM và tình trạng Docker/WSL.
- Đề xuất cách thực hiện: triển khai trực tiếp từng nhiệm vụ trong phiên làm việc, kiểm thử trước khi chuyển nhiệm vụ. Nếu chủ dự án chọn giao việc cho nhiều agent thì dùng phương án review tương ứng; chưa tự khởi chạy agent.
