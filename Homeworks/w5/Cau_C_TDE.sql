USE master;
GO

-- 1. Tạo master key (nếu chưa có)
IF NOT EXISTS (SELECT 1 FROM sys.symmetric_keys WHERE name = '##MS_DatabaseMasterKey##')
BEGIN
    CREATE MASTER KEY ENCRYPTION BY PASSWORD = '123';
END
GO

-- 2. Tạo certificate để bảo vệ database encryption key
CREATE CERTIFICATE QLBongDa_TDE_Cert 
WITH SUBJECT = 'QLBongDa TDE Certificate';
GO

-- 3. Tạo database encryption key (DEK) trong CSDL QLBongDa
USE QLBongDa;
GO

CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE QLBongDa_TDE_Cert;
GO

-- 4. Bật TDE cho CSDL
ALTER DATABASE QLBongDa
SET ENCRYPTION ON;
GO

-- 5. Kiểm tra trạng thái mã hóa
SELECT 
    db.name,
    db.is_encrypted,
    dm.encryption_state,
    dm.percent_complete,
    dm.key_algorithm,
    dm.key_length
FROM 
    sys.databases db
    LEFT JOIN sys.dm_database_encryption_keys dm
        ON db.database_id = dm.database_id
WHERE 
    db.name = 'QLBongDa';
GO

-- 6. Backup certificate và private key (QUAN TRỌNG để có thể phục hồi sau này)
USE master;
GO

BACKUP CERTIFICATE QLBongDa_TDE_Cert
TO FILE = 'QLBongDa_TDE_Cert.cer'
WITH PRIVATE KEY (
    FILE = 'QLBongDa_TDE_Cert.pvk',
    ENCRYPTION BY PASSWORD = '123'
);
GO