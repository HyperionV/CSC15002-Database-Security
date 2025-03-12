import pyodbc
import sys
import os


def main():
    # Create output file
    output_file = os.path.join(os.path.dirname(
        __file__), 'final_test_output.txt')
    with open(output_file, 'w') as f:
        f.write("Starting final decryption test...\n")

        try:
            # Connect to the database
            connection_string = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=QLSVNhom;Trusted_Connection=yes;'
            f.write(f"Connection string: {connection_string}\n")

            conn = pyodbc.connect(connection_string)
            f.write("Connection successful!\n")

            # Use a known working username and password
            username = "ttbinh"
            password = "pass123"

            # Get employee ID for the authenticated user
            cursor = conn.cursor()
            auth_query = """
            SELECT MANV, HOTEN
            FROM NHANVIEN
            WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
            """
            cursor.execute(auth_query, (username, password))
            result = cursor.fetchone()

            if not result:
                f.write(f"Authentication failed for user {username}\n")
                return 1

            employee_id = result.MANV
            employee_name = result.HOTEN
            f.write(
                f"Authentication successful for employee: {employee_id} ({employee_name})\n")

            # Test SP_SEL_BANGDIEM_BY_MALOP
            f.write("\nTesting SP_SEL_BANGDIEM_BY_MALOP...\n")
            class_id = "L001"  # Use a known class ID

            try:
                # Call the stored procedure directly
                cursor.execute(f"EXEC SP_SEL_BANGDIEM_BY_MALOP @MALOP = ?, @MANV = ?, @MK = ?",
                               (class_id, employee_id, password))

                # Get column names
                columns = [column[0]
                           for column in cursor.description] if cursor.description else []
                f.write(f"Result columns: {columns}\n")

                # Fetch results
                rows = cursor.fetchall()
                f.write(f"Retrieved {len(rows)} grades for class {class_id}\n")

                for row in rows:
                    f.write("  Grade:\n")
                    for i, col in enumerate(columns):
                        value = row[i]
                        value_type = type(value).__name__
                        f.write(f"    {col}: {value} (type: {value_type})\n")
            except Exception as e:
                f.write(f"Error calling SP_SEL_BANGDIEM_BY_MALOP: {str(e)}\n")

            # Test SP_SEL_BANGDIEM_BY_MASV
            f.write("\nTesting SP_SEL_BANGDIEM_BY_MASV...\n")
            student_id = "SV001"  # Use a known student ID

            try:
                # Call the stored procedure directly
                cursor.execute(f"EXEC SP_SEL_BANGDIEM_BY_MASV @MASV = ?, @MANV = ?, @MK = ?",
                               (student_id, employee_id, password))

                # Get column names
                columns = [column[0]
                           for column in cursor.description] if cursor.description else []
                f.write(f"Result columns: {columns}\n")

                # Fetch results
                rows = cursor.fetchall()
                f.write(
                    f"Retrieved {len(rows)} grades for student {student_id}\n")

                for row in rows:
                    f.write("  Grade:\n")
                    for i, col in enumerate(columns):
                        value = row[i]
                        value_type = type(value).__name__
                        f.write(f"    {col}: {value} (type: {value_type})\n")
            except Exception as e:
                f.write(f"Error calling SP_SEL_BANGDIEM_BY_MASV: {str(e)}\n")

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
