import pyodbc
import logging
import base64
from typing import Optional, Dict, List, Any, Tuple, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_connector')


class DatabaseConnector:
    """Database connection manager for the QLSV application."""

    def __init__(self, server: str = 'localhost', database: str = 'QLSVNhom',
                 username: Optional[str] = None, password: Optional[str] = None,
                 trusted_connection: bool = True):
        """Initialize database connection parameters."""
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.trusted_connection = trusted_connection
        self.conn = None

    def get_connection_string(self) -> str:
        """Generate the connection string based on authentication method."""
        if self.trusted_connection:
            return f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'
        else:
            return f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'

    def connect(self) -> bool:
        """Establish a connection to the database."""
        try:
            connection_string = self.get_connection_string()
            self.conn = pyodbc.connect(connection_string)
            logger.info("Database connection established successfully")
            return True
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {str(e)}")
            return False

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except pyodbc.Error as e:
                logger.error(f"Error closing database connection: {str(e)}")
            finally:
                self.conn = None

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict]]:
        """Execute a SQL query and return results as a list of dictionaries."""
        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # If it's a SELECT query, return results
            if query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results

            # For INSERT, UPDATE, DELETE, commit changes
            self.conn.commit()
            return []

        except pyodbc.Error as e:
            logger.error(f"Query execution error: {str(e)}, Query: {query}")
            self.conn.rollback()
            return None

    def execute_sproc(self, sproc_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[Union[List[Dict], Dict[str, Any], bool]]:
        """Execute a stored procedure and return the results."""
        try:
            # Connect to the database
            conn = pyodbc.connect(self.get_connection_string())
            cursor = conn.cursor()

            # Log the stored procedure call
            logger.info(f"Executing stored procedure: {sproc_name}")
            logger.info(f"Parameters: {params}")

            # Handle parameters if provided
            if params:
                # Separate input and output parameters
                input_params = {}
                output_params = {}

                for key, value in params.items():
                    if value is None and key.startswith('@') is False and key.endswith('_OUTPUT') is False:
                        # This is likely an output parameter
                        output_params[key] = value
                    else:
                        input_params[key] = value

                # Build parameter string for the SQL call
                param_string = ""
                param_values = []

                # For pyodbc, we need to use a different approach for output parameters
                if output_params:
                    # Create a stored procedure call with both input and output parameters
                    param_placeholders = []

                    # Add input parameters
                    for key in input_params:
                        param_placeholders.append(f"@{key}=?")
                        param_values.append(input_params[key])

                    # Add output parameters
                    for key in output_params:
                        param_placeholders.append(f"@{key}=? OUTPUT")
                        # Add a placeholder value for the output parameter
                        param_values.append(None)

                    param_string = ", ".join(param_placeholders)
                else:
                    # Only input parameters
                    for key, value in input_params.items():
                        param_string += f"@{key}=?, "
                        param_values.append(value)

                    # Remove trailing comma and space
                    if param_string:
                        param_string = param_string[:-2]

                # Execute the stored procedure
                call_string = f"EXEC {sproc_name} {param_string}"

                logger.info(f"SQL to execute: {call_string}")
                logger.info(f"Parameter values: {param_values}")

                cursor.execute(call_string, param_values)

                # For output parameters, we need to fetch them from the cursor
                # This is a workaround since pyodbc doesn't directly support OUTPUT parameters
                # We'll check if there are any results that might contain our output values
                if output_params:
                    # Try to get output parameters from result set
                    # Some stored procedures return output parameters as a single-row result set
                    if cursor.description:
                        columns = [column[0] for column in cursor.description]
                        row = cursor.fetchone()
                        if row:
                            # If we have output parameters in the result set
                            for i, col_name in enumerate(columns):
                                # Remove @ prefix if present
                                clean_name = col_name.replace('@', '')
                                if clean_name in output_params:
                                    output_params[clean_name] = row[i]
            else:
                # Execute without parameters
                cursor.execute(f"EXEC {sproc_name}")

            # Check if the stored procedure returns result set
            results = []
            if cursor.description:
                columns = [column[0] for column in cursor.description]

                # Log column information for debugging
                column_info = []
                for i, column in enumerate(cursor.description):
                    col_name = column[0]
                    col_type = type(column[1])
                    col_size = column[2]
                    col_precision = column[3]
                    column_info.append(
                        f"{col_name} (type: {col_type}, size: {col_size}, precision: {col_precision})")
                logger.info(f"Result columns: {column_info}")

                # Fetch all rows
                rows = cursor.fetchall()
                for row in rows:
                    result_dict = {}
                    for i, value in enumerate(row):
                        # Convert datetime objects to string for easier handling
                        if isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        result_dict[columns[i]] = value
                    results.append(result_dict)

                logger.info(
                    f"Stored procedure executed successfully. Result count: {len(results)}")

                # Close cursor and connection
                cursor.close()
                conn.close()

                # If we have output parameters, include them in the result
                if 'output_params' in locals() and output_params:
                    return {
                        'results': results,
                        'output_params': output_params
                    }
                return results
            else:
                # No result set, but might have output parameters
                logger.info(
                    "Stored procedure executed successfully. No result set.")

                # Commit the transaction for INSERT/UPDATE/DELETE operations
                conn.commit()

                # Close cursor and connection
                cursor.close()
                conn.close()

                # If we have output parameters, return them
                if 'output_params' in locals() and output_params:
                    return {
                        'output_params': output_params
                    }
                # Return True instead of None to indicate success
                return True

        except Exception as e:
            logger.error(
                f"Unexpected error executing stored procedure {sproc_name}: {str(e)}")
            raise

    # Convenience methods for specific stored procedures

    def authenticate_employee(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate an employee using the SP_SEL_PUBLIC_NHANVIEN stored procedure."""
        try:
            # logger.info(f"Attempting authentication for user: {username}")

            # # Try direct SQL approach instead of stored procedure
            # direct_query = """
            # SELECT
            #     MANV,
            #     HOTEN,
            #     EMAIL,
            #     DECRYPTBYASYMKEY(ASYMKEY_ID('AsymKey_NhanVien'), LUONG) AS DECRYPTED_BINARY
            # FROM NHANVIEN
            # WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
            # """

            # # Execute the direct SQL query
            # direct_results = self.execute_query(
            #     direct_query, (username, password))

            # if direct_results and len(direct_results) > 0:
            #     employee = direct_results[0]
            #     logger.info(
            #         f"Retrieved employee data (direct query): {employee}")

            #     # Remove the binary data from results before returning
            #     if 'DECRYPTED_BINARY' in employee:
            #         del employee['DECRYPTED_BINARY']

            #     return employee

            params = {'TENDN': username, 'MK': password}
            logger.info(f"params original: {params}")
            results = self.execute_sproc('SP_SEL_PUBLIC_NHANVIEN', params)
            logger.info(f"SP results: {results}")

            # Handle the case where results is a boolean (True) instead of a list
            if isinstance(results, bool):
                # Try a direct query approach as fallback
                query = """
                SELECT MANV, HOTEN, EMAIL
                FROM NHANVIEN
                WHERE TENDN = ? AND MATKHAU = HASHBYTES('SHA1', ?)
                """
                direct_results = self.execute_query(
                    query, (username, password))
                if direct_results and len(direct_results) > 0:
                    employee = direct_results[0]
                    logger.info(
                        f"Retrieved employee data (direct query fallback): {employee}")
                    # Set a default LUONGCB value since we can't decrypt it this way
                    employee['LUONGCB'] = 0
                    return employee
                return None

            if results and isinstance(results, list) and len(results) > 0:
                employee = results[0]
                logger.info(
                    f"Retrieved employee data (original SP): {employee}")

                # Handle the LUONGCB field
                if 'LUONGCB' in employee:
                    if employee['LUONGCB'] is None:
                        employee['LUONGCB'] = 0
                        logger.warning("LUONGCB is NULL, defaulted to 0")
                    else:
                        # Ensure it's an integer
                        try:
                            employee['LUONGCB'] = int(employee['LUONGCB'])
                            logger.info(
                                f"Successfully converted LUONGCB to int: {employee['LUONGCB']}")
                            return employee
                        except (ValueError, TypeError) as e:
                            logger.error(
                                f"Failed to convert LUONGCB to int: {employee['LUONGCB']}, error: {str(e)}")
                else:
                    logger.warning("LUONGCB field not found in results")

            return None
        except Exception as e:
            logger.error(f"Error in authenticate_employee: {str(e)}")
            return None

    def get_classes(self) -> Optional[List[Dict]]:
        """Get all classes using SP_SEL_LOP stored procedure."""
        return self.execute_sproc('SP_SEL_LOP')

    def get_classes_by_employee(self, manv: str) -> Optional[List[Dict]]:
        """Get classes managed by a specific employee."""
        params = {'MANV': manv}
        return self.execute_sproc('SP_SEL_LOP_BY_MANV', params)

    def check_class_managed_by_employee(self, malop: str, manv: str) -> bool:
        """
        Check if a class is already managed by the specified employee.

        Args:
            malop (str): Class ID to check
            manv (str): Employee ID to check

        Returns:
            bool: True if class is managed by employee, False otherwise
        """
        if not malop or not manv:
            logger.warning(
                "Empty class ID or employee ID provided to check_class_managed_by_employee")
            return False

        # Use direct query approach
        try:
            logger.info(
                f"Using direct query to check if class {malop} is managed by employee {manv}")
            query = "SELECT 1 FROM LOP WHERE MALOP = ? AND MANV = ?"
            results = self.execute_query(query, (malop, manv))
            exists = results is not None and len(results) > 0
            logger.info(
                f"Direct query result for class {malop} managed by employee {manv}: {exists}")
            return exists
        except Exception as e:
            logger.error(
                f"Query failed for class {malop} and employee {manv}: {str(e)}")
            return False

    def add_class(self, malop: str, tenlop: str, manv: str):
        """
        Add a new class to the database.

        Args:
            malop (str): Class ID
            tenlop (str): Class name
            manv (str): Employee ID who manages the class

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If employee doesn't exist or class already exists
        """
        logger.info(f"Checking if employee {manv} exists")
        if not self.check_employee_exists(manv):
            logger.warning(f"Employee {manv} does not exist")
            raise ValueError(
                f"Nhân viên có mã {manv} không tồn tại trong hệ thống")

        # Check if class already exists
        logger.info(f"Checking if class {malop} exists")
        if self.check_class_exists(malop):
            logger.warning(f"Class {malop} already exists")
            raise ValueError(f"Lớp có mã {malop} đã tồn tại trong hệ thống")

        # Check if class is already managed by this employee
        logger.info(f"Checking if class {malop} is managed by employee {manv}")
        if self.check_class_managed_by_employee(malop, manv):
            logger.warning(
                f"Class {malop} is already managed by employee {manv}")
            raise ValueError(
                f"Lớp có mã {malop} đã được quản lý bởi nhân viên {manv}")

        # All checks passed, proceed with adding the class
        logger.info(f"All checks passed, adding class {malop}")
        params = {'MALOP': malop, 'TENLOP': tenlop, 'MANV': manv}
        result = self.execute_sproc('SP_INS_LOP', params)
        logger.info(f"Add class result: {result}")
        return result

    def check_employee_exists(self, manv: str) -> bool:
        """
        Check if an employee exists in the database.

        Args:
            manv (str): Employee ID to check

        Returns:
            bool: True if employee exists, False otherwise
        """
        if not manv:
            logger.warning(
                "Empty employee ID provided to check_employee_exists")
            return False

        # # First try with stored procedure
        # try:
        #     logger.info(
        #         f"Checking if employee {manv} exists using stored procedure")
        #     params = {'MANV': manv, 'RESULT': None}
        #     result = self.execute_sproc('SP_CHECK_EMPLOYEE', params)

        #     if isinstance(result, dict) and 'output_params' in result:
        #         exists = bool(result['output_params'].get('RESULT', False))
        #         logger.info(
        #             f"Stored procedure result for employee {manv} existence: {exists}")
        #         return exists

        #     logger.warning(
        #         f"Stored procedure did not return expected output parameters for employee {manv}")
        #     # If we get here, the stored procedure didn't return the expected format
        #     # We'll use the direct query approach instead of returning False immediately
        # except Exception as e:
        #     logger.error(
        #         f"Error executing stored procedure to check if employee {manv} exists: {str(e)}")
        #     # Continue to fallback query

        # Fallback to direct query
        try:
            logger.info(
                f"Falling back to direct query to check if employee {manv} exists")
            query = "SELECT 1 FROM NHANVIEN WHERE MANV = ?"
            results = self.execute_query(query, (manv,))
            exists = results is not None and len(results) > 0
            logger.info(
                f"Direct query result for employee {manv} existence: {exists}")
            return exists
        except Exception as inner_e:
            logger.error(
                f"Final fallback query failed for employee {manv}: {str(inner_e)}")
            return False

    def check_class_exists(self, malop: str) -> bool:
        """
        Check if a class exists in the database.

        Args:
            malop (str): Class ID to check

        Returns:
            bool: True if class exists, False otherwise
        """
        if not malop:
            logger.warning("Empty class ID provided to check_class_exists")
            return False

        # Use direct query approach
        try:
            logger.info(
                f"Using direct query to check if class {malop} exists")
            query = "SELECT 1 FROM LOP WHERE MALOP = ?"
            results = self.execute_query(query, (malop,))
            exists = results is not None and len(results) > 0
            logger.info(
                f"Direct query result for class {malop} existence: {exists}")
            return exists
        except Exception as inner_e:
            logger.error(
                f"Query failed for class {malop}: {str(inner_e)}")
            return False

    def update_class(self, malop, tenlop, manv):
        """
        Update class information.

        Args:
            malop (str): Class ID to update
            tenlop (str): New class name
            manv (str): New employee ID who manages the class

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If employee doesn't exist or class doesn't exist
        """
        # Check if employee exists
        if not self.check_employee_exists(manv):
            raise ValueError(
                f"Nhân viên có mã {manv} không tồn tại trong hệ thống")

        # Check if class exists
        if not self.check_class_exists(malop):
            raise ValueError(f"Lớp có mã {malop} không tồn tại trong hệ thống")

        # All checks passed, proceed with updating the class
        params = {'MALOP': malop, 'TENLOP': tenlop, 'MANV': manv}
        return self.execute_sproc('SP_UPD_LOP', params)

    def delete_class(self, malop: str) -> bool:
        """Delete a class."""
        params = {'MALOP': malop}
        result = self.execute_sproc('SP_DEL_LOP', params)
        return result is not None

    def check_employee_manages_class(self, manv: str, malop: str) -> bool:
        """Check if an employee manages a specific class."""
        try:
            # Instead of relying on output parameters which are problematic with pyodbc,
            # let's use a direct query approach
            query = """
            SELECT COUNT(*) AS is_manager 
            FROM LOP 
            WHERE MALOP = ? AND MANV = ?
            """
            result = self.execute_query(query, (malop, manv))

            if result and len(result) > 0:
                return result[0]['is_manager'] > 0
            return False
        except Exception as e:
            logger.error(f"Error checking if employee manages class: {str(e)}")
            return False

    def get_students_by_class(self, malop: str) -> Optional[List[Dict]]:
        """Get students by class."""
        params = {'MALOP': malop}
        return self.execute_sproc('SP_SEL_SINHVIEN_BY_MALOP', params)

    def get_student_by_id(self, masv: str) -> Optional[Dict]:
        """Get a single student by ID."""
        try:
            params = {'MASV': masv}
            result = self.execute_sproc('SP_SEL_SINHVIEN_BY_ID', params)

            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting student by ID: {e}")
            return None

    def add_student(self, masv: str, hoten: str, ngaysinh: str, diachi: str,
                    malop: str, tendn: str, mk: str) -> bool:
        """Add a new student."""
        params = {
            'MASV': masv,
            'HOTEN': hoten,
            'NGAYSINH': ngaysinh,
            'DIACHI': diachi,
            'MALOP': malop,
            'TENDN': tendn,
            'MK': mk
        }
        result = self.execute_sproc('SP_INS_SINHVIEN', params)
        return result is not None

    def update_student(self, masv: str, hoten: str, ngaysinh: str,
                       diachi: str, malop: str) -> bool:
        """Update student information."""
        params = {
            'MASV': masv,
            'HOTEN': hoten,
            'NGAYSINH': ngaysinh,
            'DIACHI': diachi,
            'MALOP': malop
        }
        result = self.execute_sproc('SP_UPD_SINHVIEN', params)
        return result is not None

    def delete_student(self, masv: str) -> bool:
        """Delete a student."""
        params = {'MASV': masv}
        result = self.execute_sproc('SP_DEL_SINHVIEN', params)
        return result is not None

    def add_grade(self, masv: str, mahp: str, diemthi: float, manv: str) -> bool:
        """Add a grade with encryption."""
        params = {
            'MASV': masv,
            'MAHP': mahp,
            'DIEMTHI': diemthi,
            'MANV': manv
        }
        result = self.execute_sproc('SP_INS_BANGDIEM', params)
        return result is not None

    def update_grade(self, masv: str, mahp: str, diemthi: float, manv: str) -> bool:
        """Update a grade with encryption."""
        params = {
            'MASV': masv,
            'MAHP': mahp,
            'DIEMTHI': diemthi,
            'MANV': manv
        }
        result = self.execute_sproc('SP_UPD_BANGDIEM', params)
        return result is not None

    def get_grades_by_class(self, malop: str, manv: Optional[str] = None, password: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get grades for students in a class.

        Args:
            malop (str): Class ID
            manv (Optional[str]): Employee ID for asymmetric key decryption
            password (Optional[str]): Password for asymmetric key decryption

        Returns:
            Optional[List[Dict]]: List of grade records or None if error
        """
        # Import here to avoid circular import
        from session import EmployeeSession

        # Get employee session
        employee_session = EmployeeSession()

        # Use provided parameters or get from session
        manv = manv or employee_session.employee_id
        password = password or employee_session.password

        # Check if we have the required parameters
        if not manv or not password:
            logger.error(
                "Missing employee ID or password for grade decryption")
            return None

        # Set up parameters for stored procedure
        params = {
            'MALOP': malop,
            'MANV': manv,
            'MK': password
        }

        logger.info(f"Getting grades for class {malop} with employee {manv}")
        results = self.execute_sproc('SP_SEL_BANGDIEM_BY_MALOP', params)

        # Handle the case where results is a boolean (True) instead of a list
        if isinstance(results, bool):
            logger.warning(
                "Stored procedure returned boolean instead of results")
            return []

        # Handle NULL values from TRY_CAST
        if results and isinstance(results, list):
            for result in results:
                if 'DIEMTHI' in result and result['DIEMTHI'] is None:
                    result['DIEMTHI'] = 0.0

        return results

    def get_grades_by_student(self, masv: str, manv: Optional[str] = None, password: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get grades for a student.

        Args:
            masv (str): Student ID
            manv (Optional[str]): Employee ID for asymmetric key decryption
            password (Optional[str]): Password for asymmetric key decryption

        Returns:
            Optional[List[Dict]]: List of grade records or None if error
        """
        # Import here to avoid circular import
        from session import EmployeeSession

        # Get employee session
        employee_session = EmployeeSession()

        # Use provided parameters or get from session
        manv = manv or employee_session.employee_id
        password = password or employee_session.password

        # Check if we have the required parameters
        if not manv or not password:
            logger.error(
                "Missing employee ID or password for grade decryption")
            return None

        # Set up parameters for stored procedure
        params = {
            'MASV': masv,
            'MANV': manv,
            'MK': password
        }

        logger.info(f"Getting grades for student {masv} with employee {manv}")
        results = self.execute_sproc('SP_SEL_BANGDIEM_BY_MASV', params)

        # Handle the case where results is a boolean (True) instead of a list
        if isinstance(results, bool):
            logger.warning(
                "Stored procedure returned boolean instead of results")
            return []

        # Handle NULL values from TRY_CAST
        if results and isinstance(results, list):
            for result in results:
                if 'DIEMTHI' in result and result['DIEMTHI'] is None:
                    result['DIEMTHI'] = 0.0  # Default to 0.0 for NULL grades

        return results

    def authenticate_employee_with_client_encryption(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate an employee using client-side encryption.

        Args:
            username: Employee username
            password: Employee password

        Returns:
            Employee data dictionary or None if authentication fails
        """
        try:
            # Create crypto manager
            from crypto_utils import CryptoManager
            crypto_mgr = CryptoManager()

            # Hash the password on the client side
            hashed_password = crypto_mgr.hash_password(password)
            logger.info(
                f"Client-side hashed password (hex): {hashed_password.hex()}")

            # Use direct SQL query instead of stored procedure
            query = """
            SELECT 
                MANV,
                HOTEN,
                EMAIL,
                LUONG
            FROM NHANVIEN
            WHERE TENDN = ? AND MATKHAU = ?
            """

            # Execute the query with both parameters properly passed
            results = self.execute_query(
                query, (username, pyodbc.Binary(hashed_password)))

            logger.info(
                f"Authentication query results count: {len(results) if results else 0}")

            if results and len(results) > 0:
                employee = results[0]
                logger.info(
                    f"Retrieved encrypted employee data: {employee['MANV']}")

                # Store the encrypted salary for later decryption
                if 'LUONG' in employee and employee['LUONG']:
                    employee['ENCRYPTED_LUONG'] = employee['LUONG']
                    # Clear the encrypted value from the main field
                    employee['LUONG'] = None

                return employee

            return None

        except Exception as e:
            logger.error(
                f"Error in authenticate_employee_with_client_encryption: {str(e)}")
            return None

    def add_employee_with_client_encryption(
        self,
        manv: str,
        hoten: str,
        email: str,
        luong: int,
        tendn: str,
        password: str
    ) -> bool:
        """
        Add a new employee with client-side encryption.

        Args:
            manv: Employee ID
            hoten: Employee name
            email: Employee email
            luong: Employee salary (plaintext)
            tendn: Employee username
            password: Employee password (plaintext)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create crypto manager
            from crypto_utils import CryptoManager
            crypto_mgr = CryptoManager()

            # Generate key pair
            private_key_path, public_key_pem = crypto_mgr.generate_key_pair(
                manv, password)

            # Log the public key for debugging
            logger.info(
                f"Generated public key (first 50 chars): {public_key_pem[:50]}...")

            # Hash the password
            hashed_password = crypto_mgr.hash_password(password)
            logger.info(f"Hashed password (hex): {hashed_password.hex()}")

            # Encrypt the salary using the public key
            encrypted_salary = crypto_mgr.encrypt_data(
                public_key_pem, str(luong))
            logger.info(
                f"Encrypted salary (first 20 bytes hex): {encrypted_salary.hex()[:40]}...")

            # Use direct SQL INSERT instead of stored procedure
            query = """
            INSERT INTO NHANVIEN (MANV, HOTEN, EMAIL, LUONG, TENDN, MATKHAU, PUBKEY)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            # Execute the query
            self.execute_query(
                query, (manv, hoten, email, pyodbc.Binary(encrypted_salary), tendn,
                        pyodbc.Binary(hashed_password), public_key_pem))  # Store the actual public key PEM

            logger.info(f"Added employee with client-side encryption: {manv}")
            return True

        except Exception as e:
            logger.error(
                f"Error in add_employee_with_client_encryption: {str(e)}")
            return False

    def decrypt_employee_salary(self, employee_data: Dict, password: str) -> Optional[int]:
        """
        Decrypt an employee's salary using their private key.

        Args:
            employee_data: Employee data dictionary with ENCRYPTED_LUONG field
            password: Employee password to unlock the private key

        Returns:
            Decrypted salary as integer or None if decryption fails
        """
        try:
            if 'ENCRYPTED_LUONG' not in employee_data or not employee_data['ENCRYPTED_LUONG']:
                logger.warning("No encrypted salary data to decrypt")
                return None

            manv = employee_data.get('MANV')
            if not manv:
                logger.error("No employee ID in employee data")
                return None

            # Create crypto manager
            from crypto_utils import CryptoManager
            crypto_mgr = CryptoManager()

            # Load the private key
            private_key = crypto_mgr.load_private_key(manv, password)
            if not private_key:
                logger.error(f"Failed to load private key for employee {manv}")
                return None

            # Get the encrypted salary
            encrypted_salary = employee_data['ENCRYPTED_LUONG']

            # Decrypt the salary
            decrypted_salary_str = crypto_mgr.decrypt_data(
                private_key, encrypted_salary)

            # Convert to integer
            decrypted_salary = int(decrypted_salary_str)

            logger.info(f"Successfully decrypted salary for employee {manv}")
            return decrypted_salary

        except Exception as e:
            logger.error(f"Error decrypting employee salary: {str(e)}")
            return None

    def get_employees(self) -> Optional[List[Dict]]:
        """Get all employees."""
        try:
            query = """
            SELECT MANV, HOTEN, EMAIL, LUONG, PUBKEY
            FROM NHANVIEN
            """
            results = self.execute_query(query)
            return results
        except Exception as e:
            logger.error(f"Error getting employees: {str(e)}")
            return None

    def add_grade_with_client_encryption(self, masv: str, mahp: str, encrypted_grade: str, manv: str) -> bool:
        """
        Add a grade with client-side encryption.

        Args:
            masv: Student ID
            mahp: Course ID
            encrypted_grade: Grade encrypted on the client side (base64 encoded)
            manv: Employee ID who is adding the grade

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert base64 string to binary for SQL
            binary_grade = base64.b64decode(encrypted_grade)

            # Convert to hexadecimal for SQL parameter
            hex_grade = '0x' + binary_grade.hex()

            # Use direct query with binary parameter
            query = """
            INSERT INTO BANGDIEM (MASV, MAHP, DIEMTHI)
            VALUES (?, ?, {})
            """.format(hex_grade)

            # Execute the query
            self.execute_query(query, (masv, mahp))

            logger.info(
                f"Added grade with client-side encryption for student {masv}, course {mahp}")
            return True

        except Exception as e:
            logger.error(
                f"Error in add_grade_with_client_encryption: {str(e)}")
            return False

    def update_grade_with_client_encryption(self, masv: str, mahp: str, encrypted_grade: str, manv: str) -> bool:
        """
        Update a grade with client-side encryption.

        Args:
            masv: Student ID
            mahp: Course ID
            encrypted_grade: Grade encrypted on the client side (base64 encoded)
            manv: Employee ID who is updating the grade

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert base64 string to binary for SQL
            binary_grade = base64.b64decode(encrypted_grade)

            # Convert to hexadecimal for SQL parameter
            hex_grade = '0x' + binary_grade.hex()

            # Use direct query with binary parameter
            query = """
            UPDATE BANGDIEM
            SET DIEMTHI = {}
            WHERE MASV = ? AND MAHP = ?
            """.format(hex_grade)

            # Execute the query
            self.execute_query(query, (masv, mahp))

            logger.info(
                f"Updated grade with client-side encryption for student {masv}, course {mahp}")
            return True

        except Exception as e:
            logger.error(
                f"Error in update_grade_with_client_encryption: {str(e)}")
            return False

    def get_grades_with_client_encryption(self, class_id: str) -> Optional[List[Dict]]:
        """
        Get grades for students in a class with encrypted data.

        Args:
            class_id: Class ID

        Returns:
            List of grade records with encrypted grade data
        """
        try:
            # Query to get grades for students in a class
            query = """
            SELECT BD.MASV, S.HOTEN AS TENSV, BD.MAHP, HP.TENHP, BD.DIEMTHI
            FROM BANGDIEM BD
            JOIN SINHVIEN S ON BD.MASV = S.MASV
            JOIN HOCPHAN HP ON BD.MAHP = HP.MAHP
            WHERE S.MALOP = ?
            """

            results = self.execute_query(query, (class_id,))

            # Process the results to handle binary data
            if results:
                for result in results:
                    if 'DIEMTHI' in result and result['DIEMTHI']:
                        # Store the encrypted grade for later decryption
                        result['ENCRYPTED_DIEMTHI'] = result['DIEMTHI']
                        # Placeholder for encrypted data
                        result['DIEMTHI'] = "***"

            return results

        except Exception as e:
            logger.error(
                f"Error in get_grades_with_client_encryption: {str(e)}")
            return None
