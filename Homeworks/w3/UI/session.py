from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('session')


class EmployeeSession:
    """Singleton class to manage employee session data across the application."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmployeeSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not getattr(self, "_initialized", False):
            self._employee_data = None
            self._authenticated = False
            self._password = None  # Add new attribute to store password
            self._initialized = True
            logger.info("Employee session initialized")

    def login(self, employee_data: Dict[str, Any], password: Optional[str] = None) -> bool:
        """
        Set the employee session data after successful authentication.

        Args:
            employee_data (Dict[str, Any]): Employee data from authentication
            password (Optional[str]): Employee's password for asymmetric key operations

        Returns:
            bool: True if login successful, False otherwise
        """
        if not employee_data or 'MANV' not in employee_data:
            logger.error("Invalid employee data provided for login")
            return False

        self._employee_data = employee_data
        self._authenticated = True
        self._password = password  # Store password temporarily for decryption operations
        logger.info(
            f"Employee {employee_data.get('MANV')} logged in successfully")
        return True

    def logout(self) -> None:
        """Clear the session data on logout."""
        self._employee_data = None
        self._authenticated = False
        self._password = None  # Clear password on logout
        logger.info("Employee logged out")

    @property
    def is_authenticated(self) -> bool:
        """Check if an employee is currently authenticated."""
        return self._authenticated and self._employee_data is not None

    @property
    def employee_id(self) -> Optional[str]:
        """Get the current employee ID (MANV)."""
        if self.is_authenticated:
            return self._employee_data.get('MANV')
        return None

    @property
    def employee_name(self) -> Optional[str]:
        """Get the current employee name."""
        if self.is_authenticated:
            return self._employee_data.get('HOTEN')
        return None

    @property
    def password(self) -> Optional[str]:
        """Get the current employee password for asymmetric key operations."""
        return self._password if self.is_authenticated else None

    @property
    def employee_data(self) -> Optional[Dict[str, Any]]:
        """Get all employee data (read-only)."""
        if self.is_authenticated:
            return self._employee_data.copy()  # Return a copy to prevent modifications
        return None

    def can_manage_class(self, class_id: str, db_connector) -> bool:
        """Check if the current employee can manage the specified class."""
        if not self.is_authenticated:
            return False

        employee_id = self.employee_id
        if not employee_id:
            return False

        # Call the stored procedure to check permission
        return db_connector.check_employee_manages_class(employee_id, class_id)
