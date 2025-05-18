"""
TLS/SSL utilities for the LLM Training Platform.

This module provides functions for setting up TLS/SSL for secure communication.
"""

import os
import ssl
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from src.common.config.settings import settings

logger = logging.getLogger(__name__)


class TLSManager:
    """
    Manager for TLS/SSL configuration.
    
    This class provides methods for setting up TLS/SSL for secure communication.
    """
    
    def __init__(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_path: Optional[str] = None,
    ):
        """
        Initialize the TLS manager.
        
        Args:
            cert_path: Path to the SSL certificate file. If not provided, it will be read from
                       environment variable SSL_CERT_PATH.
            key_path: Path to the SSL key file. If not provided, it will be read from
                      environment variable SSL_KEY_PATH.
            ca_path: Path to the CA certificate file. If not provided, it will be read from
                     environment variable SSL_CA_PATH.
        """
        self.cert_path = cert_path or os.environ.get("SSL_CERT_PATH")
        self.key_path = key_path or os.environ.get("SSL_KEY_PATH")
        self.ca_path = ca_path or os.environ.get("SSL_CA_PATH")
        
        # Check if certificate and key files exist
        self._validate_paths()
    
    def _validate_paths(self) -> None:
        """
        Validate that certificate and key files exist.
        
        Raises:
            FileNotFoundError: If certificate or key file does not exist.
        """
        if self.cert_path and not Path(self.cert_path).exists():
            raise FileNotFoundError(f"SSL certificate file not found: {self.cert_path}")
        
        if self.key_path and not Path(self.key_path).exists():
            raise FileNotFoundError(f"SSL key file not found: {self.key_path}")
        
        if self.ca_path and not Path(self.ca_path).exists():
            raise FileNotFoundError(f"SSL CA certificate file not found: {self.ca_path}")
    
    def create_ssl_context(self, verify_mode: int = ssl.CERT_REQUIRED) -> ssl.SSLContext:
        """
        Create an SSL context for secure communication.
        
        Args:
            verify_mode: SSL verification mode. Default is ssl.CERT_REQUIRED.
            
        Returns:
            ssl.SSLContext: Configured SSL context.
            
        Raises:
            ValueError: If certificate or key file is not provided.
        """
        if not self.cert_path or not self.key_path:
            raise ValueError("SSL certificate and key files must be provided")
        
        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.verify_mode = verify_mode
        
        # Load certificate and key
        context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        
        # Load CA certificate if provided
        if self.ca_path:
            context.load_verify_locations(cafile=self.ca_path)
        
        # Set secure protocols and ciphers
        context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')
        
        return context
    
    def get_uvicorn_ssl_config(self) -> Dict[str, Any]:
        """
        Get SSL configuration for Uvicorn.
        
        Returns:
            Dict[str, Any]: SSL configuration for Uvicorn.
            
        Raises:
            ValueError: If certificate or key file is not provided.
        """
        if not self.cert_path or not self.key_path:
            raise ValueError("SSL certificate and key files must be provided")
        
        return {
            "ssl_keyfile": self.key_path,
            "ssl_certfile": self.cert_path,
            "ssl_ca_certs": self.ca_path,
            "ssl_version": ssl.PROTOCOL_TLS_SERVER,
        }
    
    @staticmethod
    def generate_self_signed_cert(
        cert_path: str,
        key_path: str,
        common_name: str = "localhost",
        days_valid: int = 365,
    ) -> Tuple[str, str]:
        """
        Generate a self-signed SSL certificate.
        
        Args:
            cert_path: Path to save the certificate file.
            key_path: Path to save the key file.
            common_name: Common name for the certificate. Default is "localhost".
            days_valid: Number of days the certificate is valid. Default is 365.
            
        Returns:
            Tuple[str, str]: Paths to the certificate and key files.
            
        Note:
            This method requires the OpenSSL command-line tool to be installed.
        """
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Write private key to file
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            
            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LLM Training Platform"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Security"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=days_valid)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName(common_name)]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Write certificate to file
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            logger.info(f"Generated self-signed certificate: {cert_path}")
            logger.info(f"Generated private key: {key_path}")
            
            return cert_path, key_path
        
        except ImportError:
            logger.warning("cryptography package not installed. Falling back to OpenSSL command-line tool.")
            
            # Use OpenSSL command-line tool
            import subprocess
            
            # Create directory if it doesn't exist
            cert_dir = os.path.dirname(cert_path)
            key_dir = os.path.dirname(key_path)
            
            if cert_dir:
                os.makedirs(cert_dir, exist_ok=True)
            
            if key_dir:
                os.makedirs(key_dir, exist_ok=True)
            
            # Generate private key
            subprocess.run([
                "openssl", "genrsa",
                "-out", key_path,
                "2048"
            ], check=True)
            
            # Generate certificate
            subprocess.run([
                "openssl", "req",
                "-new",
                "-x509",
                "-key", key_path,
                "-out", cert_path,
                "-days", str(days_valid),
                "-subj", f"/CN={common_name}/O=LLM Training Platform/OU=Security"
            ], check=True)
            
            logger.info(f"Generated self-signed certificate: {cert_path}")
            logger.info(f"Generated private key: {key_path}")
            
            return cert_path, key_path


# Create a global instance of the TLS manager
tls_manager = TLSManager()
