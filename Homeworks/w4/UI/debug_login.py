import pyodbc
import logging
import sys
import hashlib
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('debug_login')

# Connection string
CONNECTION_STRING = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=QLSVNhom;Trusted_Connection=yes;'


def hash_password(password):
    """Hash password using SHA1 for client-side hashing"""
    return hashlib.sha1(password.encode()).digest()


def main():
    """Debug client-side encryption login issues"""
    logger.info("Starting client-side encryption login debug")

    try:
        # Connect to database
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        logger.info("Connected to database")

        # Test credentials
        username = "testclient"
        password = "testpass"

        # First, let's create a test user with client-side hashing
        test_id = "TEST003"
        test_name = "Test Debug User"
        test_email = "debug@test.com"

        # Hash the password
        hashed_password = hash_password(password)
        logger.info(f"Hashed password (hex): {hashed_password.hex()}")

        # Create a direct insert query
        insert_query = """
        INSERT INTO NHANVIEN (MANV, HOTEN, EMAIL, LUONG, TENDN, MATKHAU, PUBKEY)
        VALUES (?, ?, ?, NULL, ?, ?, 'TEST-KEY')
        """

        try:
            # Insert the test user
            cursor.execute(insert_query, (test_id, test_name,
                           test_email, username, pyodbc.Binary(hashed_password)))
            conn.commit()
            logger.info(
                f"Test user {test_id} created with username {username}")

            # Now try to authenticate with this user
            auth_query = """
            SELECT MANV, HOTEN, EMAIL
            FROM NHANVIEN
            WHERE TENDN = ? AND MATKHAU = ?
            """

            # Verify the raw SQL being generated
            logger.info(f"Auth query: {auth_query}")

            # Authenticate
            cursor.execute(
                auth_query, (username, pyodbc.Binary(hashed_password)))

            # Get results
            results = cursor.fetchall()
            logger.info(f"Auth results count: {len(results)}")

            if results and len(results) > 0:
                logger.info(
                    f"Authentication successful for {results[0].MANV} ({results[0].HOTEN})")
                logger.success = True
            else:
                logger.info("Authentication failed")

                # Debug: check if the user exists
                cursor.execute(
                    "SELECT MANV, TENDN, MATKHAU FROM NHANVIEN WHERE TENDN = ?", (username,))
                user_results = cursor.fetchall()

                if user_results and len(user_results) > 0:
                    user = user_results[0]
                    logger.info(f"User exists: {user.MANV}, {user.TENDN}")

                    # Get the binary form of stored password for comparison
                    cursor.execute(
                        "SELECT CONVERT(VARCHAR(MAX), MATKHAU, 2) AS HEX_PW FROM NHANVIEN WHERE TENDN = ?", (username,))
                    pw_results = cursor.fetchone()
                    if pw_results:
                        logger.info(
                            f"Stored password hex: {pw_results.HEX_PW}")
                        logger.info(
                            f"Client password hex: {hashed_password.hex()}")
                else:
                    logger.info("User does not exist")

        except Exception as e:
            logger.error(f"Error during test: {str(e)}")
        finally:
            # Clean up - delete test user
            try:
                cursor.execute(
                    "DELETE FROM NHANVIEN WHERE MANV = ?", (test_id,))
                conn.commit()
                logger.info(f"Test user {test_id} deleted")
            except Exception as e:
                logger.error(f"Error deleting test user: {str(e)}")

        # Close connection
        cursor.close()
        conn.close()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
