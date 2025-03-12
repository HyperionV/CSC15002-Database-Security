-- Insert test data into LOP (5 rows)
EXEC SP_INS_LOP 'L001', N'Công nghệ thông tin K42', 'NV001';
EXEC SP_INS_LOP 'L002', N'Khoa học máy tính K42', 'NV001';
EXEC SP_INS_LOP 'L003', N'Kỹ thuật phần mềm K42', 'NV001';
EXEC SP_INS_LOP 'L004', N'An toàn thông tin K42', 'NV001';
EXEC SP_INS_LOP 'L005', N'Hệ thống thông tin K42', 'NV001';

-- Insert test data into SINHVIEN (5 rows)
EXEC SP_INS_SINHVIEN 'SV001', N'Trần Văn An', '2003-05-15', N'Hà Nội', 'L001', 'antv', 'sv123456';
EXEC SP_INS_SINHVIEN 'SV002', N'Lê Thị Bình', '2003-08-22', N'Hải Phòng', 'L001', 'binhlt', 'sv123456';
EXEC SP_INS_SINHVIEN 'SV003', N'Phạm Văn Cường', '2003-02-10', N'Đà Nẵng', 'L002', 'cuongpv', 'sv123456';
EXEC SP_INS_SINHVIEN 'SV004', N'Nguyễn Thị Dung', '2003-11-05', N'TP. Hồ Chí Minh', 'L003', 'dungnt', 'sv123456';
EXEC SP_INS_SINHVIEN 'SV005', N'Hoàng Văn Em', '2003-07-30', N'Cần Thơ', 'L004', 'emhv', 'sv123456';

-- Insert test data into HOCPHAN (5 rows)
EXEC SP_INS_HOCPHAN 'HP001', N'Cơ sở dữ liệu', 3;
EXEC SP_INS_HOCPHAN 'HP002', N'Lập trình Java', 4;
EXEC SP_INS_HOCPHAN 'HP003', N'An toàn mạng', 3;
EXEC SP_INS_HOCPHAN 'HP004', N'Trí tuệ nhân tạo', 4;
EXEC SP_INS_HOCPHAN 'HP005', N'Phân tích thiết kế hệ thống', 3;

-- Insert test data into BANGDIEM (5 rows)
-- Using the employee's key to encrypt grades
EXEC SP_INS_BANGDIEM 'SV001', 'HP001', 8.5, 'NV001';
EXEC SP_INS_BANGDIEM 'SV002', 'HP001', 7.5, 'NV001';
EXEC SP_INS_BANGDIEM 'SV003', 'HP002', 9.0, 'NV001';
EXEC SP_INS_BANGDIEM 'SV004', 'HP003', 8.0, 'NV001';
EXEC SP_INS_BANGDIEM 'SV005', 'HP004', 7.0, 'NV001';

-- Test retrieving data
-- View all classes
EXEC SP_SEL_LOP;

-- View students in class L001
EXEC SP_SEL_SINHVIEN_BY_MALOP 'L001';

-- View grades for student SV001 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MASV 'SV001', 'NV001', 'abcd12';

-- View grades for course HP001 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MAHP 'HP001', 'NV001', 'abcd12';

-- View grades for class L001 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MALOP 'L001', 'NV001', 'abcd12';

-- Test employee authentication
EXEC SP_SEL_PUBLIC_NHANVIEN 'NVA', 'abcd12';

EXEC SP_INS_PUBLIC_NHANVIEN 'NV002', N'Trần Thị Hương', 'huong@edu.vn', 9200000, 'huongtt', 'secure456';

-- Insert test data into LOP (5 rows)
EXEC SP_INS_LOP 'L006', N'Công nghệ thông tin K43', 'NV002';
EXEC SP_INS_LOP 'L007', N'Khoa học máy tính K43', 'NV002';
EXEC SP_INS_LOP 'L008', N'Kỹ thuật phần mềm K43', 'NV002';
EXEC SP_INS_LOP 'L009', N'An toàn thông tin K43', 'NV002';
EXEC SP_INS_LOP 'L010', N'Hệ thống thông tin K43', 'NV002';

-- Insert test data into SINHVIEN (5 rows)
EXEC SP_INS_SINHVIEN 'SV006', N'Lý Văn Minh', '2004-03-12', N'Hà Nội', 'L006', 'minhlv', 'sv789012';
EXEC SP_INS_SINHVIEN 'SV007', N'Vũ Thị Ngọc', '2004-06-25', N'Bắc Ninh', 'L006', 'ngocvt', 'sv789012';
EXEC SP_INS_SINHVIEN 'SV008', N'Đinh Văn Phúc', '2004-01-18', N'Thái Bình', 'L007', 'phucdv', 'sv789012';
EXEC SP_INS_SINHVIEN 'SV009', N'Mai Thị Quỳnh', '2004-09-30', N'Nghệ An', 'L008', 'quynhmt', 'sv789012';
EXEC SP_INS_SINHVIEN 'SV010', N'Trương Văn Sơn', '2004-04-05', N'Thanh Hóa', 'L009', 'sontv', 'sv789012';

-- Insert test data into HOCPHAN (5 rows)
EXEC SP_INS_HOCPHAN 'HP006', N'Lập trình Web', 4;
EXEC SP_INS_HOCPHAN 'HP007', N'Mạng máy tính', 3;
EXEC SP_INS_HOCPHAN 'HP008', N'Hệ điều hành', 3;
EXEC SP_INS_HOCPHAN 'HP009', N'Kiến trúc máy tính', 3;
EXEC SP_INS_HOCPHAN 'HP010', N'Công nghệ blockchain', 2;

-- Insert test data into BANGDIEM (5 rows)
-- Using the employee's key to encrypt grades
EXEC SP_INS_BANGDIEM 'SV006', 'HP006', 8.2, 'NV002';
EXEC SP_INS_BANGDIEM 'SV007', 'HP007', 7.8, 'NV002';
EXEC SP_INS_BANGDIEM 'SV008', 'HP008', 9.3, 'NV002';
EXEC SP_INS_BANGDIEM 'SV009', 'HP009', 6.5, 'NV002';
EXEC SP_INS_BANGDIEM 'SV010', 'HP010', 8.7, 'NV002';

-- Test retrieving data
-- View all classes
EXEC SP_SEL_LOP;

-- View students in class L006
EXEC SP_SEL_SINHVIEN_BY_MALOP 'L006';

-- View grades for student SV006 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MASV 'SV006', 'NV002', 'secure456';

-- View grades for course HP006 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MAHP 'HP006', 'NV002', 'secure456';

-- View grades for class L006 (requires employee credentials)
EXEC SP_SEL_BANGDIEM_BY_MALOP 'L006', 'NV002', 'secure456';

-- Test employee authentication
EXEC SP_SEL_PUBLIC_NHANVIEN 'huongtt', 'secure456';