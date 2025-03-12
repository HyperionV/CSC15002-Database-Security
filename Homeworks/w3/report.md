# Report: Fixing Asymmetric Key Encryption and Decryption in SQL Server

## Summary of Changes

The issue was resolved by modifying the `SP_SEL_PUBLIC_NHANVIEN` stored procedure to correctly use asymmetric key decryption. The primary problem was in how the key was referenced and how the decrypted data was processed.

## Key Issues Identified

1. **Incorrect Key Reference**: The original procedure was using `ASYMKEY_ID(PUBKEY)` which indirectly referenced the key through the PUBKEY column.

2. **Improper Type Conversion**: The original procedure used `TRY_CONVERT(INT, DECRYPTBYASYMKEY(...))` which attempted to convert binary data directly to INT.

3. **Authentication and Decryption Separation**: The procedure was mixing authentication logic with decryption logic in a way that made debugging difficult.

## Changes Made

### 1. Direct Key Identification

**Before:**
```sql
TRY_CONVERT(INT, DECRYPTBYASYMKEY(
    ASYMKEY_ID(PUBKEY), 
    LUONG, 
    @MK
)) AS LUONGCB
```

**After:**
```sql
-- Get the employee ID first
DECLARE @EmpManv VARCHAR(20);
SELECT @EmpManv = MANV FROM NHANVIEN WHERE TENDN = @TENDN AND MATKHAU = HASHBYTES('SHA1', @MK);

-- Get key ID directly
DECLARE @KeyID INT = ASYMKEY_ID(@EmpManv);
```

This change ensures we're directly referencing the asymmetric key by its name (which is stored in MANV) rather than indirectly through the PUBKEY column.

### 2. Proper Type Conversion Chain

**Before:**
```sql
TRY_CONVERT(INT, DECRYPTBYASYMKEY(...)) AS LUONGCB
```

**After:**
```sql
CAST(
    CAST(
        DECRYPTBYASYMKEY(
            @KeyID,
            LUONG, 
            @MK
        ) AS VARCHAR(20)
    ) AS INT
) AS LUONGCB
```

This change implements a two-step conversion:
1. First convert the binary result to VARCHAR
2. Then convert the VARCHAR to INT

This matches how the data was originally encrypted (converted to VARCHAR before encryption) and ensures proper type handling.

### 3. Separated Authentication from Decryption

**Before:**
```sql
IF EXISTS (SELECT 1 FROM NHANVIEN WHERE TENDN = @TENDN AND MATKHAU = HASHBYTES('SHA1', @MK))
BEGIN
    -- Decrypt and return data
END
```

**After:**
```sql
-- Get the employee ID first (authentication)
DECLARE @EmpManv VARCHAR(20);
SELECT @EmpManv = MANV FROM NHANVIEN WHERE TENDN = @TENDN AND MATKHAU = HASHBYTES('SHA1', @MK);

-- If employee found, proceed with decryption
IF @EmpManv IS NOT NULL
BEGIN
    -- Decryption logic
END
```

This change separates the authentication step from the decryption step, making the code more modular and easier to debug.

## Technical Explanation of Asymmetric Key Usage

### Encryption Process (in SP_INS_PUBLIC_NHANVIEN)

1. **Key Creation**: An asymmetric key is created for each employee using their ID as the key name:
   ```sql
   EXEC('CREATE ASYMMETRIC KEY [' + @MANV + '] WITH ALGORITHM = RSA_2048 ENCRYPTION BY PASSWORD = ''' + @MK + '''');
   ```

2. **Data Encryption**: The salary is encrypted using the public portion of the asymmetric key:
   ```sql
   SET @LUONG_ENCRYPTED = ENCRYPTBYASYMKEY(
       ASYMKEY_ID(@MANV), 
       CONVERT(VARCHAR(20), @LUONGCB)
   );
   ```

3. **Key Reference Storage**: The employee ID is stored in the PUBKEY column to reference which key to use for decryption:
   ```sql
   INSERT INTO NHANVIEN (..., PUBKEY) VALUES (..., @MANV);
   ```

### Decryption Process (in SP_SEL_PUBLIC_NHANVIEN)

1. **Authentication**: Verify user credentials using the hashed password:
   ```sql
   SELECT @EmpManv = MANV FROM NHANVIEN WHERE TENDN = @TENDN AND MATKHAU = HASHBYTES('SHA1', @MK);
   ```

2. **Key Identification**: Get the key ID directly using the employee ID:
   ```sql
   DECLARE @KeyID INT = ASYMKEY_ID(@EmpManv);
   ```

3. **Data Decryption**: Decrypt the salary using the private portion of the asymmetric key, which requires the password:
   ```sql
   DECRYPTBYASYMKEY(@KeyID, LUONG, @MK)
   ```

4. **Type Conversion**: Convert the decrypted binary data to the original data type:
   ```sql
   CAST(CAST(DECRYPTBYASYMKEY(...) AS VARCHAR(20)) AS INT)
   ```

## Conclusion

The key insight was understanding that SQL Server's asymmetric key encryption/decryption requires:

1. Proper key identification - directly referencing the key by name or ID
2. Correct password handling - providing the password for private key access
3. Appropriate type conversion - matching the conversion chain used during encryption

By implementing these changes, the salary data is now properly decrypted and returned to the user when they authenticate with the correct credentials. 