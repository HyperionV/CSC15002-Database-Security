import pyodbc
import sys
import os


def main():
    # Create output file
    output_file = os.path.join(os.path.dirname(
        __file__), 'simple_test_output.txt')
    with open(output_file, 'w') as f:
        f.write("Starting simple test...\n")

        try:
            # Connect to the database
            connection_string = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=QLSVNhom;Trusted_Connection=yes;'
            f.write(f"Connection string: {connection_string}\n")

            conn = pyodbc.connect(connection_string)
            f.write("Connection successful!\n")

            # Check all users in the database
            cursor = conn.cursor()
            cursor.execute("SELECT MANV, HOTEN, TENDN FROM NHANVIEN")

            f.write("Users in the database:\n")
            for row in cursor.fetchall():
                f.write(
                    f"  ID: {row.MANV}, Name: {row.HOTEN}, Username: {row.TENDN}\n")

            # Try to authenticate with some common passwords
            common_passwords = ['password', 'pass123',
                                '123456', 'admin', 'test', 'password123']

            cursor.execute("SELECT TENDN FROM NHANVIEN")
            usernames = [row.TENDN for row in cursor.fetchall()]

            f.write("\nTesting authentication:\n")
            for username in usernames:
                for password in common_passwords:
                    auth_query = """
                    SELECT MANV, HOTEN
                    FROM NHANVIEN
                    WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
                    """
                    cursor.execute(auth_query, (username, password))
                    result = cursor.fetchone()

                    if result:
                        f.write(
                            f"  Success: User '{username}' authenticated with password '{password}'\n")

            # Check BANGDIEM stored procedures
            f.write("\nBANGDIEM stored procedures:\n")
            cursor.execute("""
            SELECT ROUTINE_NAME
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE = 'PROCEDURE'
            AND ROUTINE_NAME LIKE '%BANGDIEM%'
            """)

            for row in cursor.fetchall():
                proc_name = row[0]
                f.write(f"  {proc_name}\n")

                # Get parameters for the procedure
                cursor.execute(f"""
                SELECT PARAMETER_NAME, PARAMETER_MODE, DATA_TYPE
                FROM INFORMATION_SCHEMA.PARAMETERS
                WHERE SPECIFIC_NAME = '{proc_name}'
                ORDER BY ORDINAL_POSITION
                """)

                f.write("    Parameters:\n")
                for param_row in cursor.fetchall():
                    f.write(
                        f"      {param_row[0]} ({param_row[1]}, {param_row[2]})\n")

            # Check BANGDIEM table structure
            f.write("\nBANGDIEM table structure:\n")
            cursor.execute(
                "IF OBJECT_ID('BANGDIEM', 'U') IS NOT NULL SELECT COUNT(*) FROM BANGDIEM ELSE SELECT -1")
            count = cursor.fetchone()[0]
            if count >= 0:
                f.write(f"  BANGDIEM table exists with {count} records\n")

                # Get column information
                cursor.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'BANGDIEM'")
                f.write("  Columns:\n")
                for col_row in cursor.fetchall():
                    f.write(f"    {col_row[0]} ({col_row[1]}")
                    if col_row[2]:
                        f.write(f", length: {col_row[2]}")
                    f.write(")\n")

                # Get sample data
                cursor.execute("SELECT TOP 5 * FROM BANGDIEM")
                columns = [column[0] for column in cursor.description]
                f.write("  Sample data:\n")

                for row in cursor.fetchall():
                    f.write("    Row:\n")
                    for i, col in enumerate(columns):
                        value = row[i]
                        value_type = type(value).__name__
                        f.write(f"      {col}: {value} (type: {value_type})\n")
            else:
                f.write("  BANGDIEM table does not exist\n")

            # Close the connection
            cursor.close()
            conn.close()
            f.write("\nConnection closed\n")

            f.write("Test completed successfully\n")

            # Print the output file path to stdout
            print(f"Output written to: {output_file}")
            return 0
        except Exception as e:
            f.write(f"Error: {str(e)}\n")
            print(f"Error: {str(e)}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
