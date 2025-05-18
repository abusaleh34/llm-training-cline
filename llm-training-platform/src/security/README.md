# Security Module

The Security Module provides comprehensive security features for the LLM Training Platform, ensuring data protection and secure communication.

## Features

### Encryption at Rest

The encryption module provides functionality to encrypt sensitive data stored on disk, including:

- Document files
- Model files
- Database backups
- Configuration files with sensitive information

The encryption is implemented using the Fernet symmetric encryption algorithm, which provides:
- AES-128-CBC encryption with PKCS7 padding
- SHA256 HMAC authentication
- Secure key derivation using PBKDF2

### Encryption in Transit (TLS/SSL)

The TLS module provides functionality to secure communication between services and with clients:

- TLS 1.2+ support with secure cipher suites
- Certificate management
- Self-signed certificate generation for development
- Proper certificate validation

## Usage

### Encrypting Data

```python
from src.security import encryption_manager

# Encrypt data
encrypted_data = encryption_manager.encrypt_data("sensitive data")

# Decrypt data
decrypted_data = encryption_manager.decrypt_data(encrypted_data)
```

### Encrypting Files

```python
from src.security import encryption_manager

# Encrypt a file
encrypted_file_path = encryption_manager.encrypt_file("/path/to/sensitive/file.txt")

# Decrypt a file
decrypted_file_path = encryption_manager.decrypt_file(encrypted_file_path)
```

### Setting up TLS/SSL

```python
from src.security import tls_manager

# Create SSL context for a server
ssl_context = tls_manager.create_ssl_context()

# Get SSL configuration for Uvicorn
ssl_config = tls_manager.get_uvicorn_ssl_config()

# Generate a self-signed certificate for development
cert_path, key_path = TLSManager.generate_self_signed_cert(
    cert_path="/path/to/cert.pem",
    key_path="/path/to/key.pem",
    common_name="localhost"
)
```

## Configuration

The security module can be configured using environment variables:

### Encryption Configuration

- `ENCRYPTION_MASTER_KEY`: Master encryption key for the platform

### TLS/SSL Configuration

- `SSL_CERT_PATH`: Path to the SSL certificate file
- `SSL_KEY_PATH`: Path to the SSL key file
- `SSL_CA_PATH`: Path to the CA certificate file

## Security Considerations

- The master encryption key should be securely stored and not included in version control
- In production, use proper certificate authorities for TLS certificates
- Regularly rotate encryption keys and certificates
- Ensure proper access controls for encrypted files
