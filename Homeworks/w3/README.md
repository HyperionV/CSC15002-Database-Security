# Quản Lý Sinh Viên

Ứng dụng quản lý sinh viên, lớp học và điểm số với bảo mật bằng mã hóa.

## Tính năng

- **Đăng nhập**: Xác thực nhân viên với tên đăng nhập và mật khẩu
- **Quản lý lớp học**: Thêm, sửa, xóa thông tin lớp học
- **Quản lý sinh viên**: Thêm, sửa, xóa thông tin sinh viên (chỉ cho các lớp do nhân viên quản lý)
- **Quản lý điểm số**: Nhập và cập nhật điểm cho sinh viên, sử dụng mã hóa asymmetric key

## Cài đặt

### Yêu cầu hệ thống

- Python 3.6 trở lên
- SQL Server (có hỗ trợ mã hóa bất đối xứng)
- Các thư viện Python (xem `requirements.txt`)

### Các bước cài đặt

1. Cài đặt cơ sở dữ liệu:

   ```sql
   -- Chạy script để tạo database và các bảng
   sqlcmd -S <server_name> -i QLSVNhom.sql
   ```

2. Cài đặt môi trường Python:

   ```bash
   # Tạo môi trường ảo (tùy chọn)
   python -m venv venv
   source venv/bin/activate  # Với Linux/Mac
   venv\Scripts\activate     # Với Windows

   # Cài đặt các thư viện
   pip install -r requirements.txt
   ```

3. Cấu hình kết nối cơ sở dữ liệu:
   - Mở file `db_connector.py` và thay đổi thông tin kết nối tại phương thức `__init__`

## Sử dụng

1. Chạy ứng dụng:

   ```bash
   python app.py
   ```

2. Đăng nhập với tài khoản nhân viên (mặc định từ QLSVNhom.sql):

   - Tên đăng nhập: `nva_user`
   - Mật khẩu: `password123`

3. Sử dụng các tính năng quản lý thông qua giao diện.

## Cấu trúc dự án

- `QLSVNhom.sql` - Script tạo cơ sở dữ liệu
- `app.py` - Tệp khởi chạy ứng dụng
- `db_connector.py` - Module kết nối cơ sở dữ liệu
- `session.py` - Module quản lý phiên đăng nhập
- `ui_components.py` - Các component giao diện chung
- `login_screen.py` - Màn hình đăng nhập
- `class_management.py` - Màn hình quản lý lớp học
- `student_management.py` - Màn hình quản lý sinh viên
- `grade_management.py` - Màn hình quản lý điểm số

## Lưu ý bảo mật

- Mật khẩu được mã hóa bằng SHA1 trong cơ sở dữ liệu
- Lương nhân viên được mã hóa bằng RSA asymmetric key
- Điểm thi được mã hóa bằng RSA asymmetric key
- Mỗi nhân viên chỉ quản lý được sinh viên trong lớp của mình

## Giấy phép

Dự án này được phát triển cho mục đích giáo dục và tuân theo giấy phép MIT.
