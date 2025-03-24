from typing import Optional, Dict, Any
import logging
from crypto_utils import CryptoManager

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
            self._password = None  # Store password for private key access
            self._private_key = None  # Store loaded private key
            self._crypto_mgr = CryptoManager()
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
        self._password = password  # Store password for private key access

        # Try to load the private key
        if password and 'MANV' in employee_data:
            try:
                self._private_key = self._crypto_mgr.load_private_key(
                    employee_data['MANV'], password)

                # If we have encrypted salary data, decrypt it
                if 'ENCRYPTED_LUONG' in employee_data and employee_data['ENCRYPTED_LUONG']:
                    try:
                        decrypted_salary = self._crypto_mgr.decrypt_data(
                            self._private_key,
                            employee_data['ENCRYPTED_LUONG']
                        )
                        employee_data['LUONG'] = int(decrypted_salary)
                        logger.info(
                            f"Successfully decrypted salary: {employee_data['LUONG']}")
                    except Exception as e:
                        logger.error(f"Failed to decrypt salary: {str(e)}")
                        employee_data['LUONG'] = 0

            except Exception as e:
                logger.error(f"Failed to load private key: {str(e)}")

        logger.info(
            f"Employee {employee_data.get('MANV')} logged in successfully")
        return True

    def logout(self) -> None:
        """Clear the session data on logout."""
        self._employee_data = None
        self._authenticated = False
        self._password = None
        self._private_key = None
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
    def private_key(self) -> Optional[Any]:
        """Get the loaded private key."""
        return self._private_key

    @property
    def employee_data(self) -> Optional[Dict[str, Any]]:
        """Get all employee data (read-only)."""
        if self.is_authenticated:
            return self._employee_data.copy()  # Return a copy to prevent modifications
        return None

    def encrypt_data(self, data: str) -> Optional[bytes]:
        """
        Encrypt data using the employee's public key.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data as bytes or None if encryption fails
        """
        if not self.is_authenticated or not self._employee_data:
            logger.error("Cannot encrypt data: No authenticated employee")
            return None

        try:
            # Get the employee's public key from the database
            # This would typically require a database query to fetch the public key
            # For now, we'll assume it's already in the employee data
            if 'PUBKEY' not in self._employee_data:
                logger.error("No public key available for encryption")
                return None

            public_key_pem = self._employee_data['PUBKEY']
            encrypted_data = self._crypto_mgr.encrypt_data(
                public_key_pem, data)
            return encrypted_data

        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return None

    def decrypt_data(self, encrypted_data: bytes) -> Optional[str]:
        """
        Decrypt data using the employee's private key.

        Args:
            encrypted_data: Encrypted data as bytes

        Returns:
            Decrypted data as string or None if decryption fails
        """
        if not self.is_authenticated or not self._private_key:
            logger.error("Cannot decrypt data: No private key available")
            return None

        try:
            decrypted_data = self._crypto_mgr.decrypt_data(
                self._private_key, encrypted_data)
            return decrypted_data

        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
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
