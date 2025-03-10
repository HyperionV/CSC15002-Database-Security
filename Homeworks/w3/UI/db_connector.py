import pyodbc
import logging
from typing import Optional, Dict, List, Any, Tuple, Union

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

    def execute_sproc(self, sproc_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[Union[List[Dict], Dict[str, Any]]]:
        """Execute a stored procedure and return results."""
        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor()

            # Build the stored procedure call
            if params:
                # Create a parameter string like "@Param1=?, @Param2=?, ..."
                param_string = ", ".join(
                    [f"@{key}=?" for key in params.keys()])
                call_string = f"{{CALL {sproc_name}({param_string})}}"

                # Execute with parameters
                cursor.execute(call_string, list(params.values()))
            else:
                # Execute without parameters
                cursor.execute(f"{{CALL {sproc_name}}}")

            # Check if the stored procedure returns results
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                # Handle output parameters if any
                output_params = {}
                for i, key in enumerate(params.keys() if params else []):
                    if cursor.description and i < len(cursor.description):
                        param_name = cursor.description[i][0]
                        if param_name.startswith('@'):
                            output_params[param_name[1:]
                                          ] = cursor.get_output_parameter_value(i)

                if output_params:
                    return {'results': results, 'output_params': output_params}
                return results

            # For procedures that don't return results
            self.conn.commit()
            return []

        except pyodbc.Error as e:
            logger.error(
                f"Stored procedure execution error: {str(e)}, Procedure: {sproc_name}")
            self.conn.rollback()
            return None

    # Convenience methods for specific stored procedures

    def authenticate_employee(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate an employee using the SP_SEL_PUBLIC_NHANVIEN stored procedure."""
        params = {'TENDN': username, 'MK': password}
        results = self.execute_sproc('SP_SEL_PUBLIC_NHANVIEN', params)

        if results and len(results) > 0:
            return results[0]  # Return the first employee record
        return None

    def get_classes(self) -> Optional[List[Dict]]:
        """Get all classes using SP_SEL_LOP stored procedure."""
        return self.execute_sproc('SP_SEL_LOP')

    def get_classes_by_employee(self, manv: str) -> Optional[List[Dict]]:
        """Get classes managed by a specific employee."""
        params = {'MANV': manv}
        return self.execute_sproc('SP_SEL_LOP_BY_MANV', params)

    def add_class(self, malop: str, tenlop: str, manv: str) -> bool:
        """Add a new class."""
        params = {'MALOP': malop, 'TENLOP': tenlop, 'MANV': manv}
        result = self.execute_sproc('SP_INS_LOP', params)
        return result is not None

    def update_class(self, malop: str, tenlop: str, manv: str) -> bool:
        """Update class information."""
        params = {'MALOP': malop, 'TENLOP': tenlop, 'MANV': manv}
        result = self.execute_sproc('SP_UPD_LOP', params)
        return result is not None

    def delete_class(self, malop: str) -> bool:
        """Delete a class."""
        params = {'MALOP': malop}
        result = self.execute_sproc('SP_DEL_LOP', params)
        return result is not None

    def check_employee_manages_class(self, manv: str, malop: str) -> bool:
        """Check if an employee manages a specific class."""
        params = {'MANV': manv, 'MALOP': malop, 'IS_MANAGER': None}
        result = self.execute_sproc('SP_CHECK_EMPLOYEE_MANAGES_CLASS', params)

        if isinstance(result, dict) and 'output_params' in result:
            return bool(result['output_params'].get('IS_MANAGER'))
        return False

    def get_students_by_class(self, malop: str) -> Optional[List[Dict]]:
        """Get students by class."""
        params = {'MALOP': malop}
        return self.execute_sproc('SP_SEL_SINHVIEN_BY_MALOP', params)

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

    def get_grades_by_student(self, masv: str) -> Optional[List[Dict]]:
        """Get grades for a student."""
        params = {'MASV': masv}
        return self.execute_sproc('SP_SEL_BANGDIEM_BY_MASV', params)

    def get_grades_by_class(self, malop: str) -> Optional[List[Dict]]:
        """Get grades for students in a class."""
        params = {'MALOP': malop}
        return self.execute_sproc('SP_SEL_BANGDIEM_BY_MALOP', params)
