USE master;
GO

-- Kill all connections to the database
ALTER DATABASE QLBongDa SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

-- Drop the database
DROP DATABASE IF EXISTS QLBongDa;
GO
-------------------------------------------------------------------------------
-- a) Tạo database QLBongDa
-------------------------------------------------------------------------------
CREATE DATABASE QLBongDa;
GO

USE QLBongDa;
GO

-------------------------------------------------------------------------------
-- b) Tạo các bảng
-------------------------------------------------------------------------------
-- Bảng CAUTHU (bỏ IDENTITY để cho phép tự nhập MACT)
CREATE TABLE CAUTHU (
    MACT INT PRIMARY KEY,
    HOTEN NVARCHAR(100) NOT NULL,
    VITRI NVARCHAR(20) NOT NULL,
    NGAYSINH DATETIME,
    DIACHI NVARCHAR(200),
    MACLB VARCHAR(5) NOT NULL,
    MAQG VARCHAR(5) NOT NULL,
    SO INT NOT NULL
);

CREATE TABLE QUOCGIA (
    MAQG VARCHAR(5) PRIMARY KEY,
    TENQG NVARCHAR(60) NOT NULL
);

CREATE TABLE CAULACBO(
    MACLB VARCHAR(5) PRIMARY KEY,
    TENCLB NVARCHAR(100) NOT NULL,
    MASAN VARCHAR(5) NOT NULL,
    MATINH VARCHAR(5) NOT NULL
);

CREATE TABLE TINH(
    MATINH VARCHAR(5) PRIMARY KEY,
    TENTINH NVARCHAR(100) NOT NULL
);

CREATE TABLE SANVD(
    MASAN VARCHAR(5) PRIMARY KEY,
    TENSAN NVARCHAR(100) NOT NULL,
    DIACHI NVARCHAR(200)
);

-- Bảng HUANLUYENVIEN (sửa DIATHOAI thành DIENTHOAI)
CREATE TABLE HUANLUYENVIEN(
    MAHLV VARCHAR(5) PRIMARY KEY,
    TENHLV NVARCHAR(100) NOT NULL,
    NGAYSINH DATETIME,
    DIACHI NVARCHAR(200),
    DIENTHOAI NVARCHAR(20),
    MAQG VARCHAR(5) NOT NULL
);

CREATE TABLE HLV_CLB(
    MAHLV VARCHAR(5),
    MACLB VARCHAR(5),
    VAITRO NVARCHAR(100) NOT NULL,
    PRIMARY KEY (MAHLV, MACLB)
);

-- Bảng TRANDAU (bỏ IDENTITY để cho phép tự nhập MATRAN)
CREATE TABLE TRANDAU(
    MATRAN INT PRIMARY KEY,
    NAM INT NOT NULL,
    VONG INT NOT NULL,
    NGAYTD DATETIME NOT NULL,
    MACLB1 VARCHAR(5) NOT NULL,
    MACLB2 VARCHAR(5) NOT NULL,
    MASAN VARCHAR(5) NOT NULL,
    KETQUA VARCHAR(5) NOT NULL
);

CREATE TABLE BANGXH(
    MACLB VARCHAR(5),
    NAM INT,
    VONG INT,
    SOTRAN INT NOT NULL,
    THANG INT NOT NULL,
    HOA INT NOT NULL,
    THUA INT NOT NULL,
    HIEUSO VARCHAR(5) NOT NULL,
    DIEM INT NOT NULL,
    HANG INT NOT NULL,
    PRIMARY KEY (MACLB, NAM, VONG)
);

-------------------------------------------------------------------------------
-- Thiết lập khóa ngoại
-------------------------------------------------------------------------------
ALTER TABLE CAUTHU 
ADD CONSTRAINT FK_CAUTHU_MACLB FOREIGN KEY (MACLB) REFERENCES CAULACBO(MACLB),
    CONSTRAINT FK_CAUTHU_MAQG FOREIGN KEY (MAQG) REFERENCES QUOCGIA(MAQG);

ALTER TABLE CAULACBO 
ADD CONSTRAINT FK_CAULACBO_MASAN FOREIGN KEY (MASAN) REFERENCES SANVD(MASAN),
    CONSTRAINT FK_CAULACBO_MATINH FOREIGN KEY (MATINH) REFERENCES TINH(MATINH);

ALTER TABLE HUANLUYENVIEN 
ADD CONSTRAINT FK_HLV_MAQG FOREIGN KEY (MAQG) REFERENCES QUOCGIA(MAQG);

ALTER TABLE HLV_CLB 
ADD CONSTRAINT FK_HLV_CLB_MAHLV FOREIGN KEY (MAHLV) REFERENCES HUANLUYENVIEN(MAHLV),
    CONSTRAINT FK_HLV_CLB_MACLB FOREIGN KEY (MACLB) REFERENCES CAULACBO(MACLB);

ALTER TABLE TRANDAU 
ADD CONSTRAINT FK_TRANDAU_MACLB1 FOREIGN KEY (MACLB1) REFERENCES CAULACBO(MACLB),
    CONSTRAINT FK_TRANDAU_MACLB2 FOREIGN KEY (MACLB2) REFERENCES CAULACBO(MACLB),
    CONSTRAINT FK_TRANDAU_MASAN FOREIGN KEY (MASAN) REFERENCES SANVD(MASAN);

ALTER TABLE BANGXH 
ADD CONSTRAINT FK_BANGXH_MACLB FOREIGN KEY (MACLB) REFERENCES CAULACBO(MACLB);

-------------------------------------------------------------------------------
-- c) Nhập liệu cho các bảng (sửa thứ tự)
-------------------------------------------------------------------------------

-- 1) QUOCGIA
INSERT INTO QUOCGIA (MAQG, TENQG)
VALUES 
('VN',  N'Việt Nam'),
('ANH', N'Anh Quốc'),
('TBN', N'Tây Ban Nha'),
('BDN', N'Bồ Đào Nha'),
('BRA', N'Brazil'),
('ITA', N'Ý'),
('THA', N'Thái Lan');

-- 2) TINH
INSERT INTO TINH (MATINH, TENTINH)
VALUES 
('BD', N'Bình Dương'),
('GL', N'Gia Lai'),
('DN', N'Đà Nẵng'),
('KH', N'Khánh Hòa'),
('PY', N'Phú Yên'),
('LA', N'Long An');

-- 3) SANVD
INSERT INTO SANVD (MASAN, TENSAN, DIACHI)
VALUES 
('GD', N'Gò Đậu',   N'123 QL1, TX Thủ Dầu Một, Bình Dương'),
('PL', N'Pleiku',   N'22 Hồ Tùng Mậu, Thống Nhất, Thị xã Pleiku, Gia Lai'),
('CL', N'Chi Lăng', N'127 Võ Văn Tần, Đà Nẵng'),
('NT', N'Nha Trang',N'128 Phan Chu Trinh, Nha Trang, Khánh Hòa'),
('TH', N'Tuy Hòa',  N'57 Trường Chinh, Tuy Hòa, Phú Yên'),
('LA', N'Long An',  N'102 Hùng Vương, Tp Tân An, Long An');

-- 4) CAULACBO (phụ thuộc TINH, SANVD)
INSERT INTO CAULACBO (MACLB, TENCLB, MASAN, MATINH)
VALUES 
('BBD', N'BECAMEX BÌNH DƯƠNG', 'GD', 'BD'),
('HAGL', N'HOÀNG ANH GIA LAI', 'PL', 'GL'),
('SDN', N'SHB ĐÀ NẴNG',        'CL', 'DN'),
('KKH', N'KHATOCO KHÁNH HÒA',  'NT', 'KH'),
('TPY', N'THÉP PHÚ YÊN',       'TH', 'PY'),
('GDT', N'GẠCH ĐỒNG TÂM LONG AN','LA','LA');

-- 5) CAUTHU (phụ thuộc CAULACBO, QUOCGIA)
INSERT INTO CAUTHU (MACT, HOTEN, VITRI, NGAYSINH, DIACHI, MACLB, MAQG, SO)
VALUES 
(1,  N'Nguyễn Vũ Phong',  N'Tiền vệ',  '1990-02-20', NULL, 'BBD', 'VN',  17),
(2,  N'Nguyễn Công Vinh', N'Tiền đạo', '1992-03-10', NULL, 'HAGL','VN',  9),
(4,  N'Trần Tấn Tài',     N'Tiền vệ',  '1989-11-12', NULL, 'BBD', 'VN',  8),
(5,  N'Phan Hồng Sơn',    N'Thủ môn',  '1991-06-10', NULL, 'HAGL','VN',  1),
(6,  N'Ronaldo',          N'Tiền vệ',  '1989-12-12', NULL, 'SDN', 'BRA', 7),
(7,  N'Robinho',          N'Tiền vệ',  '1989-12-10', NULL, 'SDN', 'BRA', 8),
(8,  N'Vidic',            N'Hậu vệ',   '1987-10-15', NULL, 'HAGL','ANH', 3),
(9,  N'Trần Văn Santos',  N'Thủ môn',  '1990-10-21', NULL, 'BBD', 'BRA', 1),
(10, N'Nguyễn Trường Sơn',N'Hậu vệ',   '1993-08-26', NULL, 'BBD', 'VN',  4);

-- 6) HUANLUYENVIEN (phụ thuộc QUOCGIA)
INSERT INTO HUANLUYENVIEN (MAHLV, TENHLV, NGAYSINH, DIACHI, DIENTHOAI, MAQG)
VALUES 
('HLV01', N'Vital',         '1955-10-15', NULL, '0918011075',  'BDN'),
('HLV02', N'Lê Huỳnh Đức',  '1972-05-20', NULL, '01223456789', 'VN'),
('HLV03', N'Kiatisuk',      '1970-12-11', NULL, '01990123456', 'THA'),
('HLV04', N'Hoàng Anh Tuấn','1970-06-10', NULL, '0989112233',  'VN'),
('HLV05', N'Trần Công Minh','1973-07-07', NULL, '0909099990',  'VN'),
('HLV06', N'Trần Văn Phúc', '1965-03-02', NULL, '01650101234', 'VN');

-- 7) HLV_CLB (phụ thuộc HLV, CLB)
INSERT INTO HLV_CLB (MAHLV, MACLB, VAITRO)
VALUES
('HLV01', 'BBD', N'HLV Chính'),
('HLV02', 'SDN', N'HLV Chính'),
('HLV03', 'HAGL',N'HLV Chính'),
('HLV04', 'KKH', N'HLV Chính'),
('HLV05', 'GDT', N'HLV Chính'),
('HLV06', 'BBD', N'HLV thủ môn');

-- 8) TRANDAU (phụ thuộc CLB, SANVD)
INSERT INTO TRANDAU (MATRAN, NAM, VONG, NGAYTD, MACLB1, MACLB2, MASAN, KETQUA)
VALUES
(1, 2009, 1, '2009-02-07', 'BBD', 'SDN', 'GD', '3-0'),
(2, 2009, 1, '2009-02-07', 'KKH','GDT', 'NT', '1-1'),
(3, 2009, 2, '2009-02-16', 'SDN','KKH', 'CL', '2-2'),
(4, 2009, 2, '2009-02-16', 'TPY','BBD', 'TH', '5-0'),
(5, 2009, 3, '2009-03-01', 'TPY','GDT', 'TH', '0-2'),
(6, 2009, 3, '2009-03-01', 'KKH','BBD', 'NT', '0-1'),
(7, 2009, 4, '2009-03-07', 'KKH','TPY', 'NT', '1-0'),
(8, 2009, 4, '2009-03-07', 'BBD','GDT', 'GD', '2-2');

-- 9) BANGXH (phụ thuộc CLB)
INSERT INTO BANGXH (MACLB, NAM, VONG, SOTRAN, THANG, HOA, THUA, HIEUSO, DIEM, HANG)
VALUES
('BBD', 2009, 1, 1, 1, 0, 0, '3-0', 3, 1),
('KKH', 2009, 1, 1, 0, 1, 0, '1-1', 1, 2),
('GDT', 2009, 1, 1, 0, 1, 0, '1-1', 1, 3),
('TPY', 2009, 1, 0, 0, 0, 0, '0-0', 0, 4),
('SDN', 2009, 1, 1, 0, 0, 1, '0-3', 0, 5),

('TPY', 2009, 2, 1, 1, 0, 0, '5-0', 3, 1),
('BBD', 2009, 2, 2, 1, 0, 1, '3-5', 3, 2),
('KKH', 2009, 2, 2, 0, 2, 0, '3-3', 2, 3),
('GDT', 2009, 2, 1, 0, 1, 0, '1-1', 1, 4),
('SDN', 2009, 2, 2, 1, 1, 0, '2-5', 1, 5),

('BBD', 2009, 3, 3, 2, 0, 1, '4-5', 6, 1),
('GDT', 2009, 3, 2, 1, 1, 0, '3-1', 4, 2),
('TPY', 2009, 3, 2, 1, 0, 1, '5-2', 3, 3),
('KKH', 2009, 3, 3, 0, 2, 1, '3-4', 2, 4),
('SDN', 2009, 3, 2, 1, 1, 0, '2-5', 1, 5),

('BBD', 2009, 4, 4, 2, 1, 1, '6-7', 7, 1),
('GDT', 2009, 4, 3, 1, 2, 0, '5-1', 5, 2),
('KKH', 2009, 4, 4, 1, 2, 1, '4-4', 5, 3),
('TPY', 2009, 4, 3, 1, 0, 2, '5-3', 3, 4),
('SDN', 2009, 4, 2, 1, 1, 0, '2-5', 1, 5);


-------------------------------------------------------------------------------
-- d) Tạo các user (và login)
-------------------------------------------------------------------------------
USE master;
GO

-- Tắt kiểm tra chính sách mật khẩu đơn giản (nếu cần)
CREATE LOGIN BDAdmin WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDAdmin FOR LOGIN BDAdmin;
ALTER ROLE db_owner ADD MEMBER BDAdmin;
GO

USE master;
GO

CREATE LOGIN BDBK WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDBK FOR LOGIN BDBK;
GRANT BACKUP DATABASE TO BDBK;
GRANT BACKUP LOG TO BDBK;
GO

USE master;
GO

CREATE LOGIN BDRead WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDRead FOR LOGIN BDRead;
ALTER ROLE db_datareader ADD MEMBER BDRead;
GO

USE master;
GO

CREATE LOGIN BDU01 WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDU01 FOR LOGIN BDU01;
GRANT CREATE TABLE TO BDU01;
GO

USE master;
GO

CREATE LOGIN BDU02 WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDU02 FOR LOGIN BDU02;
GRANT UPDATE ON SCHEMA :: dbo TO BDU02;
DENY CREATE TABLE TO BDU02;
DENY ALTER ANY SCHEMA TO BDU02;
GO

USE master;
GO

CREATE LOGIN BDU03 WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDU03 FOR LOGIN BDU03;
GRANT SELECT, INSERT, DELETE, UPDATE ON dbo.CauLacBo TO BDU03;
-- Chặn mọi quyền còn lại trên toàn schema dbo:
DENY SELECT, INSERT, DELETE, UPDATE ON SCHEMA :: dbo TO BDU03;
GO

USE master;
GO

CREATE LOGIN BDU04 WITH PASSWORD = '123'
    , CHECK_POLICY = OFF
    , CHECK_EXPIRATION = OFF;
GO

USE QLBongDa;
GO

CREATE USER BDU04 FOR LOGIN BDU04;
GRANT SELECT, INSERT, DELETE, UPDATE ON dbo.CAUTHU TO BDU04;

-- Dòng deny cột NGAYSINH và VITRI cần dùng đúng cú pháp:
DENY SELECT  (NGAYSINH) ON dbo.CAUTHU TO BDU04;
DENY UPDATE  (VITRI)    ON dbo.CAUTHU TO BDU04;

-- Chặn mọi quyền còn lại trên toàn schema dbo:
DENY SELECT, INSERT, DELETE, UPDATE ON SCHEMA :: dbo TO BDU04;
GO

USE master;
GO

IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'BDProfile')
    DROP LOGIN BDProfile;
GO

CREATE LOGIN BDProfile WITH PASSWORD = '123', CHECK_POLICY = OFF, CHECK_EXPIRATION = OFF;

USE master;
GO

IF EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'BDProfile')
    DROP USER BDProfile;
GO

CREATE USER BDProfile FOR LOGIN BDProfile;
GRANT ALTER TRACE TO BDProfile;
GO


-------------------------------------------------------------------------------
-- e) Tạo Stored Procedure SP_SEL_NO_ENCRYPT
-------------------------------------------------------------------------------
USE QLBongDa;
GO
CREATE PROCEDURE SP_SEL_NO_ENCRYPT
    @TenCLB NVARCHAR(100),  
    @TenQG  NVARCHAR(100)     
AS
BEGIN
    SET NOCOUNT ON;  

    SELECT CT.MACT, CT.HOTEN, CT.NGAYSINH, CT.DIACHI, CT.VITRI        
    FROM CAUTHU CT
    JOIN CAULACBO CLB ON CT.MACLB = CLB.MACLB  
    JOIN QUOCGIA QG  ON CT.MAQG  = QG.MAQG       
    WHERE 
        CLB.TENCLB = @TenCLB  
        AND QG.TENQG = @TenQG;  
END;
GO

------------------------------------------------------------------------------- 
-- f) Tạo Stored Procedure SP_SEL_ENCRYPT
-------------------------------------------------------------------------------
USE QLBongDa;
GO
CREATE PROCEDURE SP_SEL_ENCRYPT
    @TenCLB NVARCHAR(100),  
    @TenQG  NVARCHAR(100)     
WITH ENCRYPTION 
AS
BEGIN
    SET NOCOUNT ON;  

    SELECT CT.MACT, CT.HOTEN, CT.NGAYSINH, CT.DIACHI, CT.VITRI   
    FROM CAUTHU CT
    JOIN CAULACBO CLB ON CT.MACLB = CLB.MACLB  
    JOIN QUOCGIA QG  ON CT.MAQG  = QG.MAQG       
    WHERE 
        CLB.TENCLB = @TenCLB 
        AND QG.TENQG = @TenQG;  
END;
GO

-------------------------------------------------------------------------------
-- g) Thực thi Stored Procedure
-------------------------------------------------------------------------------
EXEC SP_SEL_NO_ENCRYPT N'SHB Đà Nẵng', N'Brazil';
EXEC SP_SEL_ENCRYPT    N'SHB Đà Nẵng', N'Brazil';
GO

-- Nhận xét:
--  + Cả 2 SP trả về kết quả cầu thủ (MãCT, Họ Tên, Ngày Sinh, Địa Chỉ, Vị Trí)
--    của CLB "SHB Đà Nẵng" và quốc tịch "Brazil".
--  + SP_SEL_ENCRYPT bị mã hóa, không xem được nội dung bằng sp_helptext
--    hoặc sys.sql_modules.
--  + SP_SEL_NO_ENCRYPT xem được nội dung, dễ dàng kiểm tra/sửa đổi.

-------------------------------------------------------------------------------
-- h) Để encrypt tất cả các stored procedure trong CSDL trước khi cài đặt cho khách hàng, ta có thể thực hiện theo các bước sau:
-------------------------------------------------------------------------------
DROP TABLE #TempProcs;
GO
-- 1. Tạo bảng tạm để lưu tên các stored procedure
CREATE TABLE #TempProcs (
    proc_name sysname
);

-- 2. Lấy danh sách các stored procedure chưa được encrypt

INSERT INTO #TempProcs
SELECT name 
FROM sys.procedures 
WHERE OBJECT_DEFINITION(OBJECT_ID) IS NOT NULL -- loại trừ các stored procedure đã được encrypt
AND is_ms_shipped = 0  -- Loại trừ các stored procedure của hệ thống

SELECT * FROM #TempProcs

-- 3. Dùng cursor để duyệt và encrypt từng procedure
DECLARE @procName sysname;
DECLARE @sql nvarchar(max);

DECLARE proc_cursor CURSOR FOR
SELECT proc_name FROM #TempProcs;

OPEN proc_cursor;
FETCH NEXT FROM proc_cursor INTO @procName;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = OBJECT_DEFINITION(OBJECT_ID(@procName));
    
    -- Thêm encryption vào procedure
    SET @sql = REPLACE(@sql, 'CREATE PROCEDURE', 'ALTER PROCEDURE');
    SET @sql = REPLACE(@sql, 'CREATE PROC', 'ALTER PROCEDURE');
    
    IF @sql NOT LIKE '%WITH ENCRYPTION%'
        SET @sql = REPLACE(@sql, 'AS', 'WITH ENCRYPTION AS');
    
    -- Thực thi procedure đã được encrypt
    EXEC(@sql);
    
    FETCH NEXT FROM proc_cursor INTO @procName;
END

CLOSE proc_cursor;
DEALLOCATE proc_cursor;

-- 4. Xóa bảng tạm
DROP TABLE #TempProcs;
GO

-------------------------------------------------------------------------------
-- i) 
-------------------------------------------------------------------------------
USE QLBongDa;
GO

CREATE VIEW vCau1 AS
SELECT CT.MACT, CT.SO, CT.HOTEN, CT.NGAYSINH, CT.DIACHI, CT.VITRI
FROM CAUTHU CT 
JOIN CAULACBO CLB ON CT.MACLB = CLB.MACLB
JOIN QUOCGIA QG ON CT.MAQG = QG.MAQG
WHERE CLB.TENCLB = N'SHB ĐÀ NẴNG' AND QG.TENQG = N'Brazil';
GO

CREATE VIEW vCau2 AS
SELECT TD.MATRAN, TD.NGAYTD, TD.MASAN, CLB1.TENCLB AS TENCLB1, 
       CLB2.TENCLB AS TENCLB2, TD.KETQUA
FROM TRANDAU TD
JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
WHERE TD.NAM = 2009 AND TD.VONG = 3;
GO

CREATE VIEW vCau3 AS
SELECT HLV.MAHLV, HLV.TENHLV, HLV.NGAYSINH, HLV.DIACHI, 
       HLV_CLB.VAITRO, CLB.TENCLB
FROM HUANLUYENVIEN HLV
JOIN HLV_CLB ON HLV.MAHLV = HLV_CLB.MAHLV
JOIN CAULACBO CLB ON HLV_CLB.MACLB = CLB.MACLB
JOIN QUOCGIA QG ON HLV.MAQG = QG.MAQG
WHERE QG.TENQG = N'Việt Nam';
GO

CREATE VIEW vCau4 AS
SELECT CLB.MACLB, CLB.TENCLB, SVD.TENSAN, SVD.DIACHI,
       COUNT(CT.MACT) AS SoLuongCTNuocNgoai
FROM CAULACBO CLB
JOIN SANVD SVD ON CLB.MASAN = SVD.MASAN
JOIN CAUTHU CT ON CLB.MACLB = CT.MACLB
JOIN QUOCGIA QG ON CT.MAQG = QG.MAQG
WHERE QG.TENQG != N'Việt Nam'
GROUP BY CLB.MACLB, CLB.TENCLB, SVD.TENSAN, SVD.DIACHI
HAVING COUNT(CT.MACT) > 2;
GO

CREATE VIEW vCau5 AS
SELECT T.TENTINH, COUNT(CT.MACT) AS SoLuongCauThuTienDao
FROM TINH T
JOIN CAULACBO CLB ON T.MATINH = CLB.MATINH
JOIN CAUTHU CT ON CLB.MACLB = CT.MACLB
WHERE CT.VITRI = N'Tiền đạo'
GROUP BY T.TENTINH;
GO

CREATE VIEW vCau6 AS
SELECT CLB.TENCLB, T.TENTINH
FROM CAULACBO CLB
JOIN TINH T ON CLB.MATINH = T.MATINH
JOIN BANGXH BXH ON CLB.MACLB = BXH.MACLB
WHERE BXH.VONG = 3 AND BXH.NAM = 2009 AND BXH.HANG = 1;
GO

CREATE VIEW vCau7 AS
SELECT HLV.TENHLV
FROM HUANLUYENVIEN HLV
JOIN HLV_CLB ON HLV.MAHLV = HLV_CLB.MAHLV
WHERE HLV.DIENTHOAI IS NULL;
GO

CREATE VIEW vCau8 AS
SELECT HLV.TENHLV
FROM HUANLUYENVIEN HLV
JOIN QUOCGIA QG ON HLV.MAQG = QG.MAQG
WHERE QG.TENQG = N'Việt Nam'
AND HLV.MAHLV NOT IN (SELECT MAHLV FROM HLV_CLB);
GO

CREATE VIEW vCau9 AS
SELECT TD.MATRAN, TD.NGAYTD, SVD.TENSAN, CLB1.TENCLB AS TENCLB1,
       CLB2.TENCLB AS TENCLB2, TD.KETQUA
FROM TRANDAU TD
JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
JOIN SANVD SVD ON TD.MASAN = SVD.MASAN
JOIN BANGXH BXH ON CLB1.MACLB = BXH.MACLB
WHERE BXH.HANG = 1 AND TD.VONG <= 3 AND TD.NAM = 2009;
GO

CREATE VIEW vCau10 AS
SELECT TD.MATRAN, TD.NGAYTD, SVD.TENSAN, CLB1.TENCLB AS TENCLB1,
       CLB2.TENCLB AS TENCLB2, TD.KETQUA
FROM TRANDAU TD
JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
JOIN SANVD SVD ON TD.MASAN = SVD.MASAN
JOIN BANGXH BXH ON CLB1.MACLB = BXH.MACLB
WHERE BXH.VONG = 3 AND BXH.NAM = 2009 
AND BXH.HANG = (SELECT MAX(HANG) FROM BANGXH WHERE VONG = 3 AND NAM = 2009);
GO

-- Phân quyền cho các user

-- Cấp quyền cho BDRead
GRANT SELECT ON vCau1 TO BDRead;
GRANT SELECT ON vCau2 TO BDRead;
GRANT SELECT ON vCau3 TO BDRead;
GRANT SELECT ON vCau4 TO BDRead;
GRANT SELECT ON vCau5 TO BDRead;
GRANT SELECT ON vCau6 TO BDRead;
GRANT SELECT ON vCau7 TO BDRead;
GRANT SELECT ON vCau8 TO BDRead;
GRANT SELECT ON vCau9 TO BDRead;
GRANT SELECT ON vCau10 TO BDRead;

-- Cấp quyền cho BDU01
GRANT SELECT ON vCau5 TO BDU01;
GRANT SELECT ON vCau6 TO BDU01;
GRANT SELECT ON vCau7 TO BDU01;
GRANT SELECT ON vCau8 TO BDU01;
GRANT SELECT ON vCau9 TO BDU01;
GRANT SELECT ON vCau10 TO BDU01;

-- Cấp quyền cho BDU03
GRANT SELECT ON vCau1 TO BDU03;
GRANT SELECT ON vCau2 TO BDU03;
GRANT SELECT ON vCau3 TO BDU03;
GRANT SELECT ON vCau4 TO BDU03;

-- Cấp quyền cho BDU04
GRANT SELECT ON vCau1 TO BDU04;
GRANT SELECT ON vCau2 TO BDU04;
GRANT SELECT ON vCau3 TO BDU04;
GRANT SELECT ON vCau4 TO BDU04;


-- Kết nối CSDL và thực thi query
-- 1. BDRead
EXECUTE AS USER = 'BDRead';
PRINT 'Current user: ' + SYSTEM_USER;
SELECT * FROM vCau1;
SELECT * FROM vCau5;
REVERT;

-- 2. BDU01
EXECUTE AS USER = 'BDU01';
PRINT 'Current user: ' + SYSTEM_USER;
SELECT * FROM vCau2;
SELECT * FROM vCau10;
REVERT;

-- 3. BDU03
EXECUTE AS USER = 'BDU03';
PRINT 'Current user: ' + SYSTEM_USER;
SELECT * FROM vCau1;
SELECT * FROM vCau2;
SELECT * FROM vCau3;
SELECT * FROM vCau4;
REVERT;

-- 4. BDU04
EXECUTE AS USER = 'BDU04';
PRINT 'Current user: ' + SYSTEM_USER;
SELECT * FROM vCau1;
SELECT * FROM vCau2;
SELECT * FROM vCau3;
SELECT * FROM vCau4;
REVERT;

-------------------------------------------------------------------------------
-- j)
-------------------------------------------------------------------------------
USE QLBongDa;
GO

-- SPCau1: Thông tin của cầu thủ thuộc một đội bóng và có quốc tịch cho trước
CREATE PROCEDURE SPCau1 
    @TenCLB NVARCHAR(100),
    @TenQG NVARCHAR(60)
AS
BEGIN
    SELECT CT.MACT, CT.SO, CT.HOTEN, CT.NGAYSINH, CT.DIACHI, CT.VITRI
    FROM CAUTHU CT 
    JOIN CAULACBO CLB ON CT.MACLB = CLB.MACLB
    JOIN QUOCGIA QG ON CT.MAQG = QG.MAQG
    WHERE CLB.TENCLB = @TenCLB AND QG.TENQG = @TenQG;
END;
GO

-- SPCau2: Kết quả các trận đấu một vòng và một mùa bóng (năm) cho trước
CREATE PROCEDURE SPCau2
    @Vong INT,
    @Nam INT
AS
BEGIN
    SELECT TD.MATRAN, TD.NGAYTD, TD.MASAN, CLB1.TENCLB AS TENCLB1, 
           CLB2.TENCLB AS TENCLB2, TD.KETQUA
    FROM TRANDAU TD
    JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
    JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
    WHERE TD.NAM = @Nam AND TD.VONG = @Vong;
END;
GO

-- SPCau3: Thông tin các huấn luyện viên với quốc tịch cho trước
CREATE PROCEDURE SPCau3
    @TenQG NVARCHAR(60)
AS
BEGIN
    SELECT HLV.MAHLV, HLV.TENHLV, HLV.NGAYSINH, HLV.DIACHI, 
           HLV_CLB.VAITRO, CLB.TENCLB
    FROM HUANLUYENVIEN HLV
    JOIN HLV_CLB ON HLV.MAHLV = HLV_CLB.MAHLV
    JOIN CAULACBO CLB ON HLV_CLB.MACLB = CLB.MACLB
    JOIN QUOCGIA QG ON HLV.MAQG = QG.MAQG
    WHERE QG.TENQG = @TenQG;
END;
GO

-- SPCau4: Thông tin câu lạc bộ và số cầu thủ nước ngoài có quốc tịch khác quốc tịch cho trước và có nhiều hơn 2 cầu thủ nước ngoài
CREATE PROCEDURE SPCau4
    @TenQG NVARCHAR(60)
AS
BEGIN
    SELECT CLB.MACLB, CLB.TENCLB, SVD.TENSAN, SVD.DIACHI,
           COUNT(CT.MACT) AS SoLuongCTNuocNgoai
    FROM CAULACBO CLB
    JOIN SANVD SVD ON CLB.MASAN = SVD.MASAN
    JOIN CAUTHU CT ON CLB.MACLB = CT.MACLB
    JOIN QUOCGIA QG ON CT.MAQG = QG.MAQG
    WHERE QG.TENQG != @TenQG
    GROUP BY CLB.MACLB, CLB.TENCLB, SVD.TENSAN, SVD.DIACHI
    HAVING COUNT(CT.MACT) > 2;
END;
GO

-- SPCau5: Số lượng cầu thủ tiền đạo của từng tỉnh  
CREATE PROCEDURE SPCau5
AS
BEGIN
    SELECT T.TENTINH, COUNT(CT.MACT) AS SoLuongCauThuTienDao
    FROM TINH T
    JOIN CAULACBO CLB ON T.MATINH = CLB.MATINH
    JOIN CAUTHU CT ON CLB.MACLB = CT.MACLB
    WHERE CT.VITRI = N'Tiền đạo'
    GROUP BY T.TENTINH;
END;
GO

-- SPCau6: CLB đứng đầu BXH vòng và năm cho trước
CREATE PROCEDURE SPCau6
    @Vong INT,
    @Nam INT
AS
BEGIN
    SELECT CLB.TENCLB, T.TENTINH
    FROM CAULACBO CLB
    JOIN TINH T ON CLB.MATINH = T.MATINH
    JOIN BANGXH BXH ON CLB.MACLB = BXH.MACLB
    WHERE BXH.VONG = @Vong AND BXH.NAM = @Nam AND BXH.HANG = 1;
END;
GO

-- SPCau7: HLV không có số điện thoại
CREATE PROCEDURE SPCau7
AS
BEGIN
    SELECT HLV.TENHLV
    FROM HUANLUYENVIEN HLV
    JOIN HLV_CLB ON HLV.MAHLV = HLV_CLB.MAHLV
    WHERE HLV.DIENTHOAI IS NULL;
END;
GO

-- SPCau8: HLV có quốc tịch cho trước chưa làm việc cho CLB nào
CREATE PROCEDURE SPCau8
    @TenQG NVARCHAR(60)
AS
BEGIN
    SELECT HLV.TENHLV
    FROM HUANLUYENVIEN HLV
    JOIN QUOCGIA QG ON HLV.MAQG = QG.MAQG
    WHERE QG.TENQG = @TenQG
    AND HLV.MAHLV NOT IN (SELECT MAHLV FROM HLV_CLB);
END;
GO

-- SPCau9: Trận đấu của đội đứng đầu BXH trong vòng và năm cho trước
CREATE PROCEDURE SPCau9
    @Vong INT,
    @Nam INT
AS
BEGIN
    SELECT TD.MATRAN, TD.NGAYTD, SVD.TENSAN, CLB1.TENCLB AS TENCLB1,
           CLB2.TENCLB AS TENCLB2, TD.KETQUA
    FROM TRANDAU TD
    JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
    JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
    JOIN SANVD SVD ON TD.MASAN = SVD.MASAN
    JOIN BANGXH BXH ON CLB1.MACLB = BXH.MACLB
    WHERE BXH.HANG = 1 AND TD.VONG <= @Vong AND TD.NAM = @Nam;
END;
GO

-- SPCau10: Trận đấu của đội đứng cuối BXH vòng và năm cho trước
CREATE PROCEDURE SPCau10
    @Vong INT,
    @Nam INT
AS
BEGIN
    SELECT TD.MATRAN, TD.NGAYTD, SVD.TENSAN, CLB1.TENCLB AS TENCLB1,
           CLB2.TENCLB AS TENCLB2, TD.KETQUA
    FROM TRANDAU TD
    JOIN CAULACBO CLB1 ON TD.MACLB1 = CLB1.MACLB
    JOIN CAULACBO CLB2 ON TD.MACLB2 = CLB2.MACLB
    JOIN SANVD SVD ON TD.MASAN = SVD.MASAN
    JOIN BANGXH BXH ON CLB1.MACLB = BXH.MACLB
    WHERE BXH.VONG = @Vong AND BXH.NAM = @Nam 
    AND BXH.HANG = (SELECT MAX(HANG) FROM BANGXH WHERE VONG = @Vong AND NAM = @Nam);
END;
GO

-- Phân quyền cho các user

-- Cấp quyền cho BDRead trên tất cả stored procedures
GRANT EXECUTE ON SPCau1 TO BDRead;
GRANT EXECUTE ON SPCau2 TO BDRead;
GRANT EXECUTE ON SPCau3 TO BDRead;
GRANT EXECUTE ON SPCau4 TO BDRead;
GRANT EXECUTE ON SPCau5 TO BDRead;
GRANT EXECUTE ON SPCau6 TO BDRead;
GRANT EXECUTE ON SPCau7 TO BDRead;
GRANT EXECUTE ON SPCau8 TO BDRead;
GRANT EXECUTE ON SPCau9 TO BDRead;
GRANT EXECUTE ON SPCau10 TO BDRead;

-- Cấp quyền cho BDU01 (SPCau5-SPCau10)
GRANT EXECUTE ON SPCau5 TO BDU01;
GRANT EXECUTE ON SPCau6 TO BDU01;
GRANT EXECUTE ON SPCau7 TO BDU01;
GRANT EXECUTE ON SPCau8 TO BDU01;
GRANT EXECUTE ON SPCau9 TO BDU01;
GRANT EXECUTE ON SPCau10 TO BDU01;

-- Cấp quyền cho BDU03 và BDU04 (SPCau1-SPCau4)
GRANT EXECUTE ON SPCau1 TO BDU03, BDU04;
GRANT EXECUTE ON SPCau2 TO BDU03, BDU04;
GRANT EXECUTE ON SPCau3 TO BDU03, BDU04;
GRANT EXECUTE ON SPCau4 TO BDU03, BDU04;

-- BDRead:
EXEC SPCau1 N'SHB Đà Nẵng', N'Brazil'     -- Thành công
EXEC SPCau9 3, 2009                       -- Thành công

-- BDU01:
EXEC SPCau3 N'Việt Nam'                   -- Lỗi: không có quyền thực thi
EXEC SPCau10 3, 2009                      -- Thành công

-- BDU03:
EXEC SPCau1 N'SHB Đà Nẵng', N'Brazil'     -- Thành công
EXEC SPCau10 3, 2009                      -- Lỗi: không có quyền thực thi
EXEC SPCau3 N'Việt Nam'                   -- Thành công
EXEC SPCau4 N'Việt Nam'                   -- Thành công

-- BDU04: 
EXEC SPCau1 N'SHB Đà Nẵng', N'Brazil'     -- Thành công
EXEC SPCau10 3, 2009                      -- Lỗi: không có quyền thực thi
EXEC SPCau3 N'Việt Nam'                   -- Thành công
EXEC SPCau4 N'Việt Nam'                   -- Thành công

