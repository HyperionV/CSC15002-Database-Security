USE MASTER;
GO

ALTER DATABASE QLSVNhom SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

DROP DATABASE IF EXISTS QLSVNhom;
GO

-- Tạo cơ sở dữ liệu QLSVNhom
CREATE DATABASE QLSVNhom;
GO

USE QLSVNhom;
GO

-- Tạo Database Master Key (DMK)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Nhom9ProVjp';
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

-- Stored Procedure để chèn dữ liệu vào bảng NHANVIEN
CREATE OR ALTER PROCEDURE SP_INS_PUBLIC_NHANVIEN
    @MANV VARCHAR(20),
    @HOTEN NVARCHAR(100),
    @EMAIL VARCHAR(20),
    @LUONGCB INT,
    @TENDN NVARCHAR(100),
    @MK NVARCHAR(50) -- Mật khẩu trước khi mã hóa
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @MATKHAU VARBINARY(MAX);
    DECLARE @LUONG_ENCRYPTED VARBINARY(MAX);
    
    -- Mã hóa mật khẩu bằng SHA1
    SET @MATKHAU = HASHBYTES('SHA1', @MK);
    
    -- Tạo asymmetric key cho nhân viên này nếu chưa tồn tại
    IF NOT EXISTS (SELECT * FROM sys.asymmetric_keys WHERE name = @MANV)
    BEGIN
        EXEC('CREATE ASYMMETRIC KEY [' + @MANV + '] 
              WITH ALGORITHM = RSA_2048 
              ENCRYPTION BY PASSWORD = ''' + @MK + '''');
    END
    
    -- Mã hóa lương sử dụng public key của nhân viên
    SET @LUONG_ENCRYPTED = ENCRYPTBYASYMKEY(
        ASYMKEY_ID(@MANV), 
        CONVERT(VARCHAR(20), @LUONGCB)
    );
    
    -- Chèn dữ liệu vào bảng NHANVIEN
    INSERT INTO NHANVIEN (MANV, HOTEN, EMAIL, LUONG, TENDN, MATKHAU, PUBKEY)
    VALUES (@MANV, @HOTEN, @EMAIL, @LUONG_ENCRYPTED, @TENDN, @MATKHAU, @MANV);
END;
GO

CREATE OR ALTER PROCEDURE SP_SEL_PUBLIC_NHANVIEN
    @TENDN NVARCHAR(100),
    @MK NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @EmpManv VARCHAR(20);
    
    SELECT @EmpManv = MANV 
    FROM NHANVIEN 
    WHERE TENDN = @TENDN 
      AND MATKHAU = HASHBYTES('SHA1', @MK);
    
    -- If employee found, proceed with decryption
    IF @EmpManv IS NOT NULL
    BEGIN
        -- Get key ID directly
        DECLARE @KeyID INT = ASYMKEY_ID(@EmpManv);
        
        -- Get employee info with decrypted salary
        SELECT 
            MANV,
            HOTEN,
            EMAIL,
            CAST(
                CAST(
                    DECRYPTBYASYMKEY(
                        @KeyID,
                        LUONG, 
                        @MK
                    ) AS VARCHAR(20)
                ) AS INT
            ) AS LUONGCB
        FROM NHANVIEN
        WHERE MANV = @EmpManv;
    END
END;
GO

USE QLSVNhom;
GO

-- =============================================
-- STORED PROCEDURES FOR CLASS MANAGEMENT
-- =============================================

-- Procedure to add a new class
CREATE OR ALTER PROCEDURE SP_INS_LOP
    @MALOP VARCHAR(20),
    @TENLOP NVARCHAR(100),
    @MANV VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO LOP (MALOP, TENLOP, MANV)
    VALUES (@MALOP, @TENLOP, @MANV);
END;
GO

-- Procedure to update class information
CREATE OR ALTER PROCEDURE SP_UPD_LOP
    @MALOP VARCHAR(20),
    @TENLOP NVARCHAR(100),
    @MANV VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE LOP
    SET TENLOP = @TENLOP,
        MANV = @MANV
    WHERE MALOP = @MALOP;
END;
GO

-- Procedure to delete a class
CREATE OR ALTER PROCEDURE SP_DEL_LOP
    @MALOP VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    DELETE FROM LOP
    WHERE MALOP = @MALOP;
END;
GO

-- Procedure to get all classes
CREATE OR ALTER PROCEDURE SP_SEL_LOP
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT L.MALOP, L.TENLOP, L.MANV, N.HOTEN AS TENNV
    FROM LOP L
    LEFT JOIN NHANVIEN N ON L.MANV = N.MANV;
END;
GO

-- Procedure to get classes managed by a specific employee
CREATE OR ALTER PROCEDURE SP_SEL_LOP_BY_MANV
    @MANV VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT L.MALOP, L.TENLOP, L.MANV, N.HOTEN AS TENNV
    FROM LOP L
    LEFT JOIN NHANVIEN N ON L.MANV = N.MANV
    WHERE L.MANV = @MANV;
END;
GO

-- Procedure to check if an employee manages a specific class
CREATE OR ALTER PROCEDURE SP_CHECK_EMPLOYEE_MANAGES_CLASS
    @MANV VARCHAR(20),
    @MALOP VARCHAR(20),
    @IS_MANAGER BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP AND MANV = @MANV)
        SET @IS_MANAGER = 1;
    ELSE
        SET @IS_MANAGER = 0;
END;
GO

-- =============================================
-- STORED PROCEDURES FOR STUDENT MANAGEMENT
-- =============================================

-- Procedure to add a new student
CREATE OR ALTER PROCEDURE SP_INS_SINHVIEN
    @MASV VARCHAR(20),
    @HOTEN NVARCHAR(100),
    @NGAYSINH DATETIME,
    @DIACHI NVARCHAR(200),
    @MALOP VARCHAR(20),
    @TENDN NVARCHAR(100),
    @MK NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @MATKHAU VARBINARY(MAX);
    
    -- Mã hóa mật khẩu bằng SHA1
    SET @MATKHAU = HASHBYTES('SHA1', @MK);
    
    INSERT INTO SINHVIEN (MASV, HOTEN, NGAYSINH, DIACHI, MALOP, TENDN, MATKHAU)
    VALUES (@MASV, @HOTEN, @NGAYSINH, @DIACHI, @MALOP, @TENDN, @MATKHAU);
END;
GO

-- Procedure to update student information
CREATE OR ALTER PROCEDURE SP_UPD_SINHVIEN
    @MASV VARCHAR(20),
    @HOTEN NVARCHAR(100),
    @NGAYSINH DATETIME,
    @DIACHI NVARCHAR(200),
    @MALOP VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE SINHVIEN
    SET HOTEN = @HOTEN,
        NGAYSINH = @NGAYSINH,
        DIACHI = @DIACHI,
        MALOP = @MALOP
    WHERE MASV = @MASV;
END;
GO

-- Procedure to delete a student
CREATE OR ALTER PROCEDURE SP_DEL_SINHVIEN
    @MASV VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    DELETE FROM SINHVIEN
    WHERE MASV = @MASV;
END;
GO

-- Procedure to get students by class
CREATE OR ALTER PROCEDURE SP_SEL_SINHVIEN_BY_MALOP
    @MALOP VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT MASV, HOTEN, NGAYSINH, DIACHI, MALOP, TENDN
    FROM SINHVIEN
    WHERE MALOP = @MALOP;
END;
GO

-- Procedure to get a student by ID
CREATE OR ALTER PROCEDURE SP_SEL_SINHVIEN_BY_ID
    @MASV VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT MASV, HOTEN, NGAYSINH, DIACHI, MALOP, TENDN
    FROM SINHVIEN
    WHERE MASV = @MASV;
END;
GO

-- Procedure to authenticate a student
CREATE OR ALTER PROCEDURE SP_SEL_SINHVIEN_AUTH
    @TENDN NVARCHAR(100),
    @MK NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT MASV, HOTEN, NGAYSINH, DIACHI, MALOP
    FROM SINHVIEN
    WHERE TENDN = @TENDN
    AND MATKHAU = HASHBYTES('SHA1', @MK);
END;
GO

-- =============================================
-- STORED PROCEDURES FOR GRADE MANAGEMENT
-- =============================================

-- Procedure to insert a grade with encryption using employee's public key
CREATE OR ALTER PROCEDURE SP_INS_BANGDIEM
    @MASV VARCHAR(20),
    @MAHP VARCHAR(20),
    @DIEMTHI FLOAT,
    @MANV VARCHAR(20) -- Employee ID for key lookup
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @DIEMTHI_ENCRYPTED VARBINARY(MAX);
    
    -- Encrypt the grade using the employee's public key
    SET @DIEMTHI_ENCRYPTED = ENCRYPTBYASYMKEY(
        ASYMKEY_ID(@MANV), -- Get key ID from employee ID
        CONVERT(VARCHAR(20), @DIEMTHI)
    );
    
    INSERT INTO BANGDIEM (MASV, MAHP, DIEMTHI)
    VALUES (@MASV, @MAHP, @DIEMTHI_ENCRYPTED);
END;
GO

CREATE OR ALTER PROCEDURE SP_UPD_BANGDIEM
    @MASV VARCHAR(20),
    @MAHP VARCHAR(20),
    @DIEMTHI FLOAT,
    @MANV VARCHAR(20) -- Employee ID for key lookup
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @DIEMTHI_ENCRYPTED VARBINARY(MAX);
    
    -- Encrypt the grade using the employee's public key
    SET @DIEMTHI_ENCRYPTED = ENCRYPTBYASYMKEY(
        ASYMKEY_ID(@MANV), -- Get key ID from employee ID
        CONVERT(VARCHAR(20), @DIEMTHI)
    );
    
    UPDATE BANGDIEM
    SET DIEMTHI = @DIEMTHI_ENCRYPTED
    WHERE MASV = @MASV AND MAHP = @MAHP;
END;
GO

-- Modify the SP_SEL_BANGDIEM_BY_MASV procedure to use the correct key for each grade
CREATE OR ALTER PROCEDURE SP_SEL_BANGDIEM_BY_MASV
    @MASV VARCHAR(20),
    @MANV VARCHAR(20),
    @MK NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the student's class and the employee who manages that class
    DECLARE @StudentClass VARCHAR(20);
    DECLARE @StudentClassManager VARCHAR(20);
    
    SELECT @StudentClass = S.MALOP
    FROM SINHVIEN S
    WHERE S.MASV = @MASV;

    SELECT @StudentClassManager = L.MANV
    FROM LOP L
    WHERE L.MALOP = @StudentClass;
    SELECT 
        BD.MASV,
        S.HOTEN AS TENSV,
        BD.MAHP,
        HP.TENHP,
        CASE 
            WHEN @MANV = @StudentClassManager THEN
                CONVERT(FLOAT, CONVERT(VARCHAR(20), DECRYPTBYASYMKEY(
                    ASYMKEY_ID(@MANV), 
                    BD.DIEMTHI,
                    @MK
                )))
            ELSE NULL -- Cannot decrypt grades encrypted by other employees
        END AS DIEMTHI,
        @StudentClassManager AS ENCRYPTED_BY
    FROM BANGDIEM BD
    JOIN SINHVIEN S ON BD.MASV = S.MASV
    JOIN HOCPHAN HP ON BD.MAHP = HP.MAHP
    WHERE BD.MASV = @MASV;

END;
GO

-- Modify the SP_SEL_BANGDIEM_BY_MAHP procedure to determine the encrypting employee based on class relationships
CREATE OR ALTER PROCEDURE SP_SEL_BANGDIEM_BY_MAHP
    @MAHP VARCHAR(20),
    @MANV VARCHAR(20),
    @MK NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        BD.MASV,
        S.HOTEN AS TENSV,
        BD.MAHP,
        HP.TENHP,
        CASE 
            -- Only decrypt if the current employee is the one who manages the student's class
            WHEN L.MANV = @MANV THEN
                CONVERT(FLOAT, CONVERT(VARCHAR(20), DECRYPTBYASYMKEY(
                    ASYMKEY_ID(@MANV), 
                    BD.DIEMTHI,
                    @MK
                )))
            ELSE NULL -- Cannot decrypt grades encrypted by other employees
        END AS DIEMTHI,
        L.MANV AS ENCRYPTED_BY
    FROM BANGDIEM BD
    JOIN SINHVIEN S ON BD.MASV = S.MASV
    JOIN HOCPHAN HP ON BD.MAHP = HP.MAHP
    JOIN LOP L ON S.MALOP = L.MALOP
    WHERE BD.MAHP = @MAHP;
END;
GO

-- Modify the SP_SEL_BANGDIEM_BY_MALOP procedure to determine the encrypting employee based on class relationships
CREATE OR ALTER PROCEDURE SP_SEL_BANGDIEM_BY_MALOP
    @MALOP VARCHAR(20),
    @MANV VARCHAR(20),
    @MK NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the employee who manages this class
    DECLARE @ClassManager VARCHAR(20);
    SELECT @ClassManager = MANV FROM LOP WHERE MALOP = @MALOP;
    
    SELECT 
        BD.MASV,
        S.HOTEN AS TENSV,
        BD.MAHP,
        HP.TENHP,
        CASE 
            -- Only decrypt if the current employee is the one who manages this class
            WHEN @MANV = @ClassManager THEN
                CONVERT(FLOAT, CONVERT(VARCHAR(20), DECRYPTBYASYMKEY(
                    ASYMKEY_ID(@MANV), 
                    BD.DIEMTHI,
                    @MK
                )))
            ELSE NULL -- Cannot decrypt grades encrypted by other employees
        END AS DIEMTHI,
        @ClassManager AS ENCRYPTED_BY
    FROM BANGDIEM BD
    JOIN SINHVIEN S ON BD.MASV = S.MASV
    JOIN HOCPHAN HP ON BD.MAHP = HP.MAHP
    WHERE S.MALOP = @MALOP;
END;
GO

-- Check if an employee exists
CREATE OR ALTER PROC SP_CHECK_EMPLOYEE @MANV VARCHAR(20), @RESULT BIT OUTPUT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM NHANVIEN WHERE MANV = @MANV)
        SET @RESULT = 1
    ELSE
        SET @RESULT = 0
END
GO

-- Check if a class exists
CREATE OR ALTER PROC SP_CHECK_CLASS_EXISTS @MALOP VARCHAR(20), @RESULT BIT OUTPUT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP)
        SET @RESULT = 1
    ELSE
        SET @RESULT = 0
END
GO

-- Check if a class is managed by a specific employee
CREATE OR ALTER PROC SP_CHECK_CLASS_MANAGED_BY_EMPLOYEE @MALOP VARCHAR(20), @MANV VARCHAR(20), @RESULT BIT OUTPUT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP AND MANV = @MANV)
        SET @RESULT = 1
    ELSE
        SET @RESULT = 0
END
GO 

-- Add a procedure to insert a course
CREATE OR ALTER PROCEDURE SP_INS_HOCPHAN
    @MAHP VARCHAR(20),
    @TENHP NVARCHAR(100),
    @SOTC INT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO HOCPHAN (MAHP, TENHP, SOTC)
    VALUES (@MAHP, @TENHP, @SOTC);
END;
GO


-- ==============================
-- Test data    
-- ==============================   

EXEC SP_INS_PUBLIC_NHANVIEN 'NV001', 'NGUYEN VAN A',
'NVA@', 3000000, 'NVA', 'abcd12'

SELECT * FROM NHANVIEN;

EXEC SP_SEL_PUBLIC_NHANVIEN 'NVA', 'abcd12'


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

-- ==============================
SELECT * FROM NHANVIEN;
SELECT * FROM LOP;
SELECT * FROM SINHVIEN;
SELECT * FROM HOCPHAN;
SELECT * FROM BANGDIEM;

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
