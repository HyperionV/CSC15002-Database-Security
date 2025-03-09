-- Tạo cơ sở dữ liệu QLSVNhom
CREATE DATABASE QLSVNhom;
GO

USE QLSVNhom;
GO

-- Tạo Database Master Key (DMK)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'YourStrongPassword123!';
GO

-- Bảng Nhân viên 
CREATE TABLE NHANVIEN (
    MANV VARCHAR(20) PRIMARY KEY,
    HOTEN NVARCHAR(100) NOT NULL,
    EMAIL VARCHAR(20),
    LUONG VARBINARY(MAX),
    TENDN NVARCHAR(100) NOT NULL UNIQUE,
    MATKHAU VARBINARY(MAX) NOT NULL,
    PUBKEY VARCHAR(20) 
);

-- Bảng Lớp
CREATE TABLE LOP (
    MALOP VARCHAR(20) PRIMARY KEY,
    TENLOP NVARCHAR(100) NOT NULL,
    MANV VARCHAR(20),
    FOREIGN KEY (MANV) REFERENCES NHANVIEN(MANV) ON DELETE SET NULL
);

-- Bảng Sinh viên 
CREATE TABLE SINHVIEN (
    MASV VARCHAR(20) PRIMARY KEY,
    HOTEN NVARCHAR(100) NOT NULL,
    NGAYSINH DATETIME,
    DIACHI NVARCHAR(200),
    MALOP VARCHAR(20), 
    TENDN NVARCHAR(100) NOT NULL UNIQUE,
    MATKHAU VARBINARY(MAX) NOT NULL,
    FOREIGN KEY (MALOP) REFERENCES LOP(MALOP) ON DELETE SET NULL
);

-- Bảng Học phần
CREATE TABLE HOCPHAN (
    MAHP VARCHAR(20) PRIMARY KEY,
    TENHP NVARCHAR(100) NOT NULL,
    SOTC INT
);

-- Bảng Bảng điểm
CREATE TABLE BANGDIEM (
    MASV VARCHAR(20),
    MAHP VARCHAR(20),
    DIEMTHI VARBINARY(MAX),
    PRIMARY KEY (MASV, MAHP),
    FOREIGN KEY (MASV) REFERENCES SINHVIEN(MASV) ON DELETE CASCADE,
    FOREIGN KEY (MAHP) REFERENCES HOCPHAN(MAHP) ON DELETE CASCADE
);

GO

-- Tạo Asymmetric Key với thuật toán RSA_2048
CREATE ASYMMETRIC KEY AsymKey_NhanVien
WITH ALGORITHM = RSA_2048; -- Sử dụng thuật toán RSA với độ dài khóa 2048 bit
GO

-- Stored Procedure để chèn dữ liệu vào bảng NHANVIEN
CREATE PROCEDURE SP_INS_PUBLIC_NHANVIEN
    @MANV VARCHAR(20),
    @HOTEN NVARCHAR(100),
    @EMAIL VARCHAR(20),
    @LUONGCB VARBINARY(MAX), -- Lương trước khi mã hóa (dạng VARBINARY)
    @TENDN NVARCHAR(100),
    @MK NVARCHAR(100) -- Mật khẩu trước khi mã hóa
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @MATKHAU VARBINARY(MAX);
    DECLARE @LUONG_ENCRYPTED VARBINARY(MAX);
    DECLARE @PUBKEY VARCHAR(20);

    -- Mã hóa mật khẩu bằng SHA1
    SET @MATKHAU = HASHBYTES('SHA1', @MK);

    -- Mã hóa lương bằng Asymmetric Key (RSA)
    SET @LUONG_ENCRYPTED = ENCRYPTBYASYMKEY(ASYMKEY_ID('AsymKey_NhanVien'), @LUONGCB);

    -- Gán giá trị PUBKEY = MANV
    SET @PUBKEY = @MANV;

    -- Chèn dữ liệu vào bảng NHANVIEN
    INSERT INTO NHANVIEN (MANV, HOTEN, EMAIL, LUONG, TENDN, MATKHAU, PUBKEY)
    VALUES (@MANV, @HOTEN, @EMAIL, @LUONG_ENCRYPTED, @TENDN, @MATKHAU, @PUBKEY);
END;
GO

CREATE PROCEDURE SP_SEL_PUBLIC_NHANVIEN
    @TENDN NVARCHAR(100), -- Tên đăng nhập
    @MK NVARCHAR(100) -- Mật khẩu (khóa bí mật để giải mã lương)
AS
BEGIN
    SET NOCOUNT ON;

    -- Biến để lưu trữ mật khẩu đã mã hóa (SHA1)
    DECLARE @MATKHAU_HASH VARBINARY(MAX);

    -- Mã hóa mật khẩu đầu vào bằng SHA1 để so sánh với mật khẩu trong bảng
    SET @MATKHAU_HASH = HASHBYTES('SHA1', @MK);

    -- Truy vấn thông tin nhân viên và giải mã lương
    SELECT 
        MANV,
        HOTEN,
        EMAIL,
        CONVERT(INT, DECRYPTBYASYMKEY(ASYMKEY_ID('AsymKey_NhanVien'), LUONG)) AS LUONGCB
    FROM NHANVIEN
    WHERE TENDN = @TENDN AND MATKHAU = @MATKHAU_HASH;
END;
GO


-- Thêm dữ liệu vào bảng NHANVIEN bằng Stored Procedure
EXEC SP_INS_PUBLIC_NHANVIEN
    @MANV = 'NV001',
    @HOTEN = N'Nguyễn Văn A',
    @EMAIL = 'nva@example.com',
    @LUONGCB = CONVERT(VARBINARY(MAX), 5000), -- Chuyển đổi lương sang VARBINARY
    @TENDN = 'nva_user',
    @MK = 'password123'; -- Mật khẩu trước khi mã hóa

EXEC SP_INS_PUBLIC_NHANVIEN
    @MANV = 'NV002',
    @HOTEN = N'Trần Thị B',
    @EMAIL = 'ttb@example.com',
    @LUONGCB = CONVERT(VARBINARY(MAX), 5000), -- Chuyển đổi lương sang VARBINARY
    @TENDN = 'ttb_user',
    @MK = 'password456'; -- Mật khẩu trước khi mã hóa

-- Xem thông tin bảng NHANVIEN sau khi thêm dữ liệu
SELECT * FROM NHANVIEN;

-- Giải mã lương để xem thông tin
SELECT 
    MANV,
    HOTEN,
    EMAIL,
    CONVERT(INT, DECRYPTBYASYMKEY(ASYMKEY_ID('AsymKey_NhanVien'), LUONG)) AS LUONG_GOC,
    TENDN,
    PUBKEY
FROM NHANVIEN;

-- Truy vấn thông tin nhân viên
EXEC SP_SEL_PUBLIC_NHANVIEN
    @TENDN = 'nva_user', -- Tên đăng nhập
    @MK = 'password123'; -- Mật khẩu