"""
Encryption utilities for the LLM Training Platform.

This module provides functions for encrypting and decrypting data at rest and in transit.
"""

import os
import base64
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from pathlib import Path

from src.common.config.settings import settings


class EncryptionManager:
    """
    Manager for encryption and decryption operations.
    
    This class provides methods for encrypting and decrypting data at rest and in transit.
    It uses Fernet symmetric encryption with keys derived from a master key.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize the encryption manager.
        
        Args:
            master_key: Master encryption key. If not provided, it will be read from environment
                        variable ENCRYPTION_MASTER_KEY or generated if not available.
        """
        self.master_key = master_key or os.environ.get("ENCRYPTION_MASTER_KEY")
        
        if not self.master_key:
            # Generate a new master key if not provided
            self.master_key = self._generate_master_key()
            os.environ["ENCRYPTION_MASTER_KEY"] = self.master_key
        
        # Initialize Fernet cipher
        self.cipher = self._initialize_cipher()
    
    def _generate_master_key(self) -> str:
        """
        Generate a new master encryption key.
        
        Returns:
            str: Base64-encoded master key.
        """
        key = Fernet.generate_key()
        return key.decode()
    
    def _initialize_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with the master key.
        
        Returns:
            Fernet: Initialized Fernet cipher.
        """
        key = self.master_key.encode()
        return Fernet(key)
    
    def derive_key(self, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive a key from the master key using PBKDF2.
        
        Args:
            salt: Salt for key derivation.
            iterations: Number of iterations for key derivation.
            
        Returns:
            bytes: Derived key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        return base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
    
    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt.
            
        Returns:
            bytes: Encrypted data.
        """
        if isinstance(data, str):
            data = data.encode()
        
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data.
            
        Returns:
            bytes: Decrypted data.
        """
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_file(self, file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Encrypt a file.
        
        Args:
            file_path: Path to the file to encrypt.
            output_path: Path to save the encrypted file. If not provided, the encrypted file
                         will be saved with the same name as the input file with '.enc' extension.
            
        Returns:
            Path: Path to the encrypted file.
        """
        file_path = Path(file_path)
        
        if not output_path:
            output_path = file_path.with_suffix(file_path.suffix + '.enc')
        else:
            output_path = Path(output_path)
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encrypt_data(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        return output_path
    
    def decrypt_file(self, file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Decrypt a file.
        
        Args:
            file_path: Path to the encrypted file.
            output_path: Path to save the decrypted file. If not provided, the decrypted file
                         will be saved with the same name as the input file without '.enc' extension.
            
        Returns:
            Path: Path to the decrypted file.
        """
        file_path = Path(file_path)
        
        if not output_path:
            if file_path.suffix == '.enc':
                output_path = file_path.with_suffix('')
            else:
                output_path = file_path.with_suffix(file_path.suffix + '.dec')
        else:
            output_path = Path(output_path)
        
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.decrypt_data(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return output_path


# Create a global instance of the encryption manager
encryption_manager = EncryptionManager()
