import logging
import sys
import traceback
import pyodbc
import os
from db_connector import DatabaseConnector
from session import EmployeeSession

# Configure logging to write to a file
log_file = os.path.join(os.path.dirname(__file__), 'test_decryption.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_decryption')


def test_decryption():
    """Test the decryption of grades using stored procedures."""
    try:
        logger.info("Starting decryption test...")

        # Create database connector
        db = DatabaseConnector()
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        logger.info("Database connection established")

        # Test authentication using direct query
        username = "nvan"  # Use a known username from the database
        password = "pass123"  # Use the corresponding password

        # Use direct query for authentication
        auth_query = """
        SELECT MANV, HOTEN, EMAIL
        FROM NHANVIEN
        WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
        """
        auth_results = db.execute_query(auth_query, (username, password))

        if not auth_results or len(auth_results) == 0:
            logger.error("Authentication failed")
            return False

        employee = auth_results[0]
        logger.info(
            f"Authentication successful for employee: {employee.get('MANV')}")

        # Create employee session
        session = EmployeeSession()
        session.login(employee, password)

        if not session.is_authenticated:
            logger.error("Session authentication failed")
            return False

        logger.info(
            f"Session authenticated for employee: {session.employee_id}")

        # Test get_grades_by_class using stored procedure
        logger.info("Testing get_grades_by_class using stored procedure...")
        class_id = "L001"  # Use a known class ID from the database

        # Call the stored procedure directly
        sp_params = {'MALOP': class_id,
                     'MANV': session.employee_id, 'MATKHAU': session.password}
        logger.info(
            f"Calling SP_SEL_BANGDIEM_BY_MALOP with params: {sp_params}")

        try:
            sp_results = db.execute_sproc(
                'SP_SEL_BANGDIEM_BY_MALOP', sp_params)
            logger.info(f"SP_SEL_BANGDIEM_BY_MALOP results: {sp_results}")

            if isinstance(sp_results, list) and len(sp_results) > 0:
                logger.info(
                    f"Successfully retrieved {len(sp_results)} grades for class {class_id}")
                for grade in sp_results:
                    logger.info(f"Grade: {grade}")
            else:
                logger.warning(
                    f"No grades found for class {class_id} or results not in expected format")
        except Exception as e:
            logger.error(f"Error calling SP_SEL_BANGDIEM_BY_MALOP: {str(e)}")
            logger.error(traceback.format_exc())

        # Test get_grades_by_student using stored procedure
        logger.info("Testing get_grades_by_student using stored procedure...")
        student_id = "SV001"  # Use a known student ID from the database

        # Call the stored procedure directly
        sp_params = {'MASV': student_id,
                     'MANV': session.employee_id, 'MATKHAU': session.password}
        logger.info(
            f"Calling SP_SEL_BANGDIEM_BY_MASV with params: {sp_params}")

        try:
            sp_results = db.execute_sproc('SP_SEL_BANGDIEM_BY_MASV', sp_params)
            logger.info(f"SP_SEL_BANGDIEM_BY_MASV results: {sp_results}")

            if isinstance(sp_results, list) and len(sp_results) > 0:
                logger.info(
                    f"Successfully retrieved {len(sp_results)} grades for student {student_id}")
                for grade in sp_results:
                    logger.info(f"Grade: {grade}")
            else:
                logger.warning(
                    f"No grades found for student {student_id} or results not in expected format")
        except Exception as e:
            logger.error(f"Error calling SP_SEL_BANGDIEM_BY_MASV: {str(e)}")
            logger.error(traceback.format_exc())

        # Test using the convenience methods in DatabaseConnector
        logger.info("Testing get_grades_by_class using convenience method...")
        try:
            grades_by_class = db.get_grades_by_class(
                class_id, session.employee_id, session.password)
            logger.info(f"get_grades_by_class results: {grades_by_class}")

            if grades_by_class and len(grades_by_class) > 0:
                logger.info(
                    f"Successfully retrieved {len(grades_by_class)} grades for class {class_id}")
                for grade in grades_by_class:
                    logger.info(f"Grade: {grade}")
            else:
                logger.warning(
                    f"No grades found for class {class_id} using convenience method")
        except Exception as e:
            logger.error(f"Error in get_grades_by_class: {str(e)}")
            logger.error(traceback.format_exc())

        logger.info("Testing get_grades_by_student using convenience method...")
        try:
            grades_by_student = db.get_grades_by_student(
                student_id, session.employee_id, session.password)
            logger.info(f"get_grades_by_student results: {grades_by_student}")

            if grades_by_student and len(grades_by_student) > 0:
                logger.info(
                    f"Successfully retrieved {len(grades_by_student)} grades for student {student_id}")
                for grade in grades_by_student:
                    logger.info(f"Grade: {grade}")
            else:
                logger.warning(
                    f"No grades found for student {student_id} using convenience method")
        except Exception as e:
            logger.error(f"Error in get_grades_by_student: {str(e)}")
            logger.error(traceback.format_exc())

        # Test logout
        logger.info("Testing logout...")
        session.logout()

        if session.is_authenticated:
            logger.error("Session still authenticated after logout")
            return False

        logger.info("Logout successful")

        logger.info("All tests completed")
        return True
    except Exception as e:
        logger.error(f"Error in test_decryption: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def test_users():
    """Test to find valid usernames and passwords in the database."""
    try:
        logger.info("Starting user test...")

        # Connect to the database
        connection_string = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=QLSVNhom;Trusted_Connection=yes;'
        logger.info(f"Connection string: {connection_string}")

        conn = pyodbc.connect(connection_string)
        logger.info("Connection successful!")

        # Check all users in the database
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MANV, HOTEN, TENDN, CONVERT(VARCHAR(100), MATKHAU, 1) AS HASH_PASSWORD FROM NHANVIEN")

        users = []
        for row in cursor.fetchall():
            user = {
                'MANV': row.MANV,
                'HOTEN': row.HOTEN,
                'TENDN': row.TENDN,
                'HASH_PASSWORD': row.HASH_PASSWORD
            }
            users.append(user)
            logger.info(f"User: {user}")

        logger.info(f"Found {len(users)} users in the database")

        # Try to authenticate with some common passwords
        common_passwords = ['password', 'pass123',
                            '123456', 'admin', 'test', 'password123']

        for user in users:
            for password in common_passwords:
                try:
                    auth_query = """
                    SELECT MANV, HOTEN, EMAIL
                    FROM NHANVIEN
                    WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
                    """
                    cursor.execute(auth_query, (user['TENDN'], password))
                    result = cursor.fetchone()

                    if result:
                        logger.info(
                            f"Authentication successful for user {user['TENDN']} with password '{password}'")
                    else:
                        logger.debug(
                            f"Authentication failed for user {user['TENDN']} with password '{password}'")
                except Exception as e:
                    logger.error(
                        f"Error authenticating user {user['TENDN']} with password '{password}': {str(e)}")

        # Check if the BANGDIEM table exists and has data
        cursor.execute(
            "IF OBJECT_ID('BANGDIEM', 'U') IS NOT NULL SELECT COUNT(*) FROM BANGDIEM ELSE SELECT -1")
        count = cursor.fetchone()[0]
        if count >= 0:
            logger.info(f"BANGDIEM table exists with {count} records")

            # Check the structure of the BANGDIEM table
            cursor.execute("SELECT TOP 1 * FROM BANGDIEM")
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                logger.info(f"BANGDIEM columns: {columns}")

                # Check if there are any stored procedures for BANGDIEM
                cursor.execute("""
                SELECT ROUTINE_NAME
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_TYPE = 'PROCEDURE'
                AND ROUTINE_NAME LIKE '%BANGDIEM%'
                """)

                procedures = []
                for row in cursor.fetchall():
                    procedures.append(row[0])

                logger.info(
                    f"Found {len(procedures)} stored procedures for BANGDIEM: {procedures}")

                # Check the parameters for each stored procedure
                for proc in procedures:
                    cursor.execute(f"""
                    SELECT PARAMETER_NAME, PARAMETER_MODE, DATA_TYPE
                    FROM INFORMATION_SCHEMA.PARAMETERS
                    WHERE SPECIFIC_NAME = '{proc}'
                    ORDER BY ORDINAL_POSITION
                    """)

                    params = []
                    for row in cursor.fetchall():
                        params.append({
                            'name': row[0],
                            'mode': row[1],
                            'type': row[2]
                        })

                    logger.info(f"Parameters for {proc}: {params}")
        else:
            logger.warning("BANGDIEM table does not exist")

        # Close the connection
        cursor.close()
        conn.close()
        logger.info("Connection closed")

        logger.info("User test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error in test_users: {str(e)}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_users()
    logger.info(
        f"Test completed with result: {'SUCCESS' if success else 'FAILURE'}")
    logger.info(f"Log file written to: {log_file}")

    # Print the log file path to stdout
    print(f"\nLog file written to: {log_file}")

    sys.exit(0 if success else 1)
