import base64
import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger('crypto_utils')


class CryptoManager:
    """Manages cryptographic operations for the client application."""

    def __init__(self, keys_dir: str = 'keys'):
        """Initialize the crypto manager with a directory for key storage."""
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
        private_key_path = os.path.join(self.keys_dir, f"{employee_id}.pem")
        encrypted_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password.encode())
        )

        with open(private_key_path, 'wb') as f:
            f.write(encrypted_private_key)

        return private_key_path, public_key_pem

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
            # Load the public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode()
            )

            # Encrypt the data
            encrypted_data = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

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
            # Decrypt the data
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

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
        return base64.b64encode(binary_data).decode('utf-8')

    @staticmethod
    def decode_from_db(encoded_data: str) -> bytes:
        """
        Decode data from database storage.

        Args:
            encoded_data: Base64 encoded string

        Returns:
            Original binary data
        """
        return base64.b64decode(encoded_data)
