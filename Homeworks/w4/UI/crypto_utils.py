import base64
import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from typing import Tuple, Optional, Dict, Any
import logging

"""
Crypto Utilities Module for Secure Data Management

This module provides cryptographic functionality for the client application, including:
1. Key pair generation and management
2. Data encryption and decryption using RSA
3. Database-friendly encoding and decoding of binary data
4. Password hashing
5. Combined operations for database storage

Usage Examples:
--------------
# Initialize the manager
crypto_mgr = CryptoManager()

# Generate a key pair
private_key_path, public_key_pem = crypto_mgr.generate_key_pair("EMP001", "password")

# Load keys
private_key = crypto_mgr.load_private_key("EMP001", "password")
public_key = crypto_mgr.load_public_key(public_key_pem)

# Encrypt and decrypt data
encrypted_data = crypto_mgr.encrypt_data(public_key_pem, "sensitive data")
decrypted_data = crypto_mgr.decrypt_data(private_key, encrypted_data)

# DB operations
db_ready_data = crypto_mgr.encrypt_data_for_db(public_key_pem, "50000")  # For DB storage
original_data = crypto_mgr.decrypt_data_from_db(private_key, db_ready_data)  # After DB retrieval
"""

logger = logging.getLogger('crypto_utils')


class CryptoManager:
    """Manages cryptographic operations for the client application."""

    def __init__(self, keys_dir: str = 'keys'):
        """Initialize the crypto manager with a directory for key storage.

        Args:
            keys_dir: Directory where private keys will be stored
        """
        self.keys_dir = keys_dir
        os.makedirs(keys_dir, exist_ok=True)

    def generate_key_pair(self, employee_id: str, password: str) -> Tuple[str, str]:
        """
        Generate an RSA key pair for an employee.

        Args:
            employee_id: Employee ID to use as the key identifier
            password: Password to encrypt the private key

        Returns:
            Tuple of (private_key_path, public_key_pem)
        """
        try:
            if not employee_id or not password:
                logger.error(
                    "Invalid employee_id or password for key generation")
                raise ValueError(
                    "Employee ID and password are required for key generation")

            # Ensure keys directory exists
            os.makedirs(self.keys_dir, exist_ok=True)

            # Generate a new RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            # Get the public key in PEM format
            public_key = private_key.public_key()
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            # Encrypt and save the private key
            private_key_path = os.path.join(
                self.keys_dir, f"{employee_id}.pem")
            encrypted_private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    password.encode())
            )

            with open(private_key_path, 'wb') as f:
                f.write(encrypted_private_key)

            logger.info(
                f"Key pair generated successfully for employee {employee_id}")
            logger.info(f"Private key saved at: {private_key_path}")

            return private_key_path, public_key_pem

        except Exception as e:
            logger.error(f"Error generating key pair: {str(e)}")
            raise

    def load_private_key(self, employee_id: str, password: str) -> Optional[rsa.RSAPrivateKey]:
        """
        Load a private key from file.

        Args:
            employee_id: Employee ID to load the key for
            password: Password to decrypt the private key

        Returns:
            RSA private key object or None if loading fails
        """
        try:
            private_key_path = os.path.join(
                self.keys_dir, f"{employee_id}.pem")

            if not os.path.exists(private_key_path):
                logger.error(f"Private key file not found: {private_key_path}")
                return None

            with open(private_key_path, 'rb') as f:
                private_key_data = f.read()

            private_key = serialization.load_pem_private_key(
                private_key_data,
                password=password.encode()
            )

            return private_key

        except Exception as e:
            logger.error(f"Error loading private key: {str(e)}")
            return None

    def load_public_key(self, public_key_pem: str) -> Optional[rsa.RSAPublicKey]:
        """
        Load a public key from a PEM string.

        Args:
            public_key_pem: Public key in PEM format

        Returns:
            RSA public key object or None if loading fails
        """
        try:
            if not public_key_pem or not isinstance(public_key_pem, str):
                logger.error("Invalid public key PEM string provided")
                return None

            # Ensure the PEM string is properly encoded
            if isinstance(public_key_pem, str):
                public_key_data = public_key_pem.encode()
            else:
                public_key_data = public_key_pem

            # Load the public key
            public_key = serialization.load_pem_public_key(public_key_data)

            return public_key

        except Exception as e:
            logger.error(f"Error loading public key: {str(e)}")
            return None

    def encrypt_data(self, public_key_pem: str, data: str) -> bytes:
        """
        Encrypt data using an RSA public key.

        Args:
            public_key_pem: Public key in PEM format
            data: String data to encrypt

        Returns:
            Encrypted data as bytes
        """
        try:
            if not public_key_pem:
                logger.error("No public key provided for encryption")
                raise ValueError("Public key is required for encryption")

            if not data:
                logger.error("No data provided for encryption")
                raise ValueError("Data is required for encryption")

            # Check data type and convert if necessary
            if not isinstance(data, str):
                data = str(data)
                logger.info(
                    f"Converted non-string data to string for encryption: {type(data).__name__}")

            # Load the public key (using our new method)
            public_key = self.load_public_key(public_key_pem)
            if not public_key:
                logger.error("Failed to load public key for encryption")
                raise ValueError("Invalid public key format")

            # Encrypt the data
            encrypted_data = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            logger.info(
                f"Data encrypted successfully. Length: {len(encrypted_data)} bytes")
            return encrypted_data

        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise

    def decrypt_data(self, private_key: rsa.RSAPrivateKey, encrypted_data: bytes) -> str:
        """
        Decrypt data using an RSA private key.

        Args:
            private_key: RSA private key object
            encrypted_data: Encrypted data as bytes

        Returns:
            Decrypted data as string
        """
        try:
            if not private_key:
                logger.error("No private key provided for decryption")
                raise ValueError("Private key is required for decryption")

            if not encrypted_data:
                logger.error("No data provided for decryption")
                raise ValueError("Encrypted data is required for decryption")

            # Check encrypted_data type and convert if necessary
            if isinstance(encrypted_data, str):
                # Assume it's a base64 encoded string
                try:
                    encrypted_data = base64.b64decode(encrypted_data)
                    logger.info(
                        "Converted string encrypted data from base64 to bytes")
                except:
                    logger.error(
                        "Failed to convert string encrypted data from base64")
                    raise ValueError(
                        "Invalid encrypted data format (not valid base64)")
            elif not isinstance(encrypted_data, bytes):
                logger.error(
                    f"Invalid encrypted data type: {type(encrypted_data).__name__}")
                raise TypeError(
                    "Encrypted data must be bytes or base64 encoded string")

            # Decrypt the data
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            logger.info("Data decrypted successfully")
            return decrypted_data.decode()

        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise

    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        Hash a password using SHA1.

        Args:
            password: Password to hash

        Returns:
            SHA1 hash of the password as bytes
        """
        if not password:
            logger.error("No password provided for hashing")
            raise ValueError("Password is required for hashing")

        return hashlib.sha1(password.encode()).digest()

    @staticmethod
    def encode_for_db(binary_data: bytes) -> str:
        """
        Encode binary data for database storage.

        Args:
            binary_data: Binary data to encode

        Returns:
            Base64 encoded string
        """
        try:
            if not binary_data:
                logger.error("No data provided for encoding")
                raise ValueError("Binary data is required for encoding")

            if not isinstance(binary_data, bytes):
                logger.warning(
                    f"Non-bytes data provided to encode_for_db: {type(binary_data).__name__}")
                if isinstance(binary_data, str):
                    # Try to encode string to bytes
                    binary_data = binary_data.encode()
                else:
                    # Try to convert to bytes
                    binary_data = bytes(binary_data)

            encoded = base64.b64encode(binary_data).decode('utf-8')
            logger.debug(
                f"Encoded {len(binary_data)} bytes to {len(encoded)} character base64 string")
            return encoded

        except Exception as e:
            logger.error(f"Error encoding binary data for DB: {str(e)}")
            raise

    @staticmethod
    def decode_from_db(encoded_data: str) -> bytes:
        """
        Decode data from database storage.

        Args:
            encoded_data: Base64 encoded string

        Returns:
            Original binary data
        """
        try:
            if not encoded_data:
                logger.error("No data provided for decoding")
                raise ValueError("Encoded data is required for decoding")

            if not isinstance(encoded_data, str):
                logger.warning(
                    f"Non-string data provided to decode_from_db: {type(encoded_data).__name__}")
                if isinstance(encoded_data, bytes):
                    # Assume it's already bytes
                    return encoded_data
                else:
                    # Try to convert to string
                    encoded_data = str(encoded_data)

            decoded = base64.b64decode(encoded_data)
            logger.debug(
                f"Decoded {len(encoded_data)} character base64 string to {len(decoded)} bytes")
            return decoded

        except Exception as e:
            logger.error(f"Error decoding data from DB: {str(e)}")
            raise

    def encrypt_data_for_db(self, public_key_pem: str, data: str) -> str:
        """
        Encrypt data and prepare it for database storage.

        Args:
            public_key_pem: Public key in PEM format
            data: String data to encrypt

        Returns:
            Base64 encoded encrypted data ready for database storage
        """
        try:
            # Encrypt the data
            encrypted_bytes = self.encrypt_data(public_key_pem, data)

            # Encode for database
            return self.encode_for_db(encrypted_bytes)

        except Exception as e:
            logger.error(f"Error in encrypt_data_for_db: {str(e)}")
            raise

    def decrypt_data_from_db(self, private_key: rsa.RSAPrivateKey, encoded_data: str) -> str:
        """
        Decrypt data retrieved from database storage.

        Args:
            private_key: RSA private key object
            encoded_data: Base64 encoded encrypted data from database

        Returns:
            Decrypted data as string
        """
        try:
            # Decode from database format
            encrypted_bytes = self.decode_from_db(encoded_data)

            # Decrypt the data
            return self.decrypt_data(private_key, encrypted_bytes)

        except Exception as e:
            logger.error(f"Error in decrypt_data_from_db: {str(e)}")
            raise
