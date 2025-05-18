# LLM Training Platform Installation Guide

This guide provides instructions for installing and setting up the LLM Training Platform.

## Prerequisites

Before installing the platform, ensure you have the following prerequisites:

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Docker Engine 20.10.0+ and Docker Compose 2.0.0+
- **Hardware Requirements**:
  - CPU: 8+ cores (16+ recommended for training)
  - RAM: 16GB+ (32GB+ recommended for training)
  - Storage: 100GB+ SSD (1TB+ recommended for large document collections)
  - GPU: NVIDIA GPU with CUDA support (for model training)
- **Network**: Internet connection for initial setup (can run air-gapped after setup)

## Installation Options

The LLM Training Platform can be installed using one of the following methods:

1. **Docker Compose**: Recommended for development and small deployments
2. **Kubernetes**: Recommended for production and scalable deployments
3. **Manual Installation**: For custom environments or when containers are not an option

## Docker Compose Installation (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/llm-training-platform.git
cd llm-training-platform
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file to configure your environment:

```
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=llm_platform
DB_USER=postgres
DB_PASSWORD=your_secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_CORS_ORIGINS=["http://localhost:3000"]

# Document Storage
DOCUMENT_STORAGE_PATH=/app/documents

# OCR Configuration
OCR_ENGINE=tesseract
OCR_LANGUAGES=eng,ara

# Security
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Logging
LOG_LEVEL=INFO
LOG_ROTATION=10 MB
```

### 3. Start the Services

```bash
docker-compose up -d
```

This will start all the required services:

- API Gateway
- Document Ingestion Service
- Database
- Document Storage
- Admin Dashboard

### 4. Initialize the Database

```bash
docker-compose exec api python -m src.scripts.init_db
```

### 5. Create an Admin User

```bash
docker-compose exec api python -m src.scripts.create_admin_user
```

Follow the prompts to create an admin user.

### 6. Access the Platform

The platform should now be accessible at:

- API: http://localhost:8000
- Admin Dashboard: http://localhost:3000

## Kubernetes Installation

For production deployments, we recommend using Kubernetes.

### 1. Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured to access your cluster
- Helm 3.0+

### 2. Add the Helm Repository

```bash
helm repo add llm-training-platform https://your-organization.github.io/llm-training-platform-charts
helm repo update
```

### 3. Configure Values

Create a `values.yaml` file with your configuration:

```yaml
global:
  environment: production
  storageClass: standard

database:
  host: your-db-host
  port: 5432
  name: llm_platform
  user: postgres
  password: your_secure_password

api:
  host: 0.0.0.0
  port: 8000
  debug: false
  corsOrigins:
    - https://your-domain.com

documentStorage:
  path: /app/documents
  size: 100Gi

security:
  jwtSecret: your_jwt_secret_key
  jwtAlgorithm: HS256
  jwtExpirationMinutes: 60

logging:
  level: INFO
  rotation: 10 MB
```

### 4. Install the Chart

```bash
helm install llm-platform llm-training-platform/llm-platform -f values.yaml
```

### 5. Initialize the Database

```bash
kubectl exec -it deployment/llm-platform-api -- python -m src.scripts.init_db
```

### 6. Create an Admin User

```bash
kubectl exec -it deployment/llm-platform-api -- python -m src.scripts.create_admin_user
```

Follow the prompts to create an admin user.

### 7. Access the Platform

The platform should now be accessible at the configured ingress or service endpoints.

## Manual Installation

For environments where containers are not an option, you can install the platform manually.

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (for Admin Dashboard)
- Tesseract OCR with Arabic language support

### 2. Clone the Repository

```bash
git clone https://github.com/your-organization/llm-training-platform.git
cd llm-training-platform
```

### 3. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file to configure your environment.

### 5. Initialize the Database

```bash
python -m src.scripts.init_db
```

### 6. Create an Admin User

```bash
python -m src.scripts.create_admin_user
```

Follow the prompts to create an admin user.

### 7. Start the Services

Start the API Gateway:

```bash
python -m src.api_gateway.main
```

Start the Document Ingestion Service:

```bash
python -m src.document_ingestion.main
```

Start other services as needed.

### 8. Set Up the Admin Dashboard

```bash
cd src/admin_dashboard
npm install
npm run build
npm start
```

### 9. Access the Platform

The platform should now be accessible at:

- API: http://localhost:8000
- Admin Dashboard: http://localhost:3000

## Troubleshooting

### Common Issues

#### Database Connection Issues

If you encounter database connection issues:

1. Verify that the database is running
2. Check the database credentials in the `.env` file
3. Ensure the database is accessible from the service containers

#### OCR Issues

If OCR is not working properly:

1. Verify that Tesseract is installed with Arabic language support
2. Check the OCR configuration in the `.env` file
3. Ensure the document files are accessible to the OCR engine

#### API Gateway Issues

If the API Gateway is not accessible:

1. Check that the API Gateway service is running
2. Verify the port configuration in the `.env` file
3. Ensure there are no firewall rules blocking the port

### Getting Help

If you encounter issues not covered in this guide:

1. Check the logs for error messages
2. Consult the [Troubleshooting Guide](../maintenance/troubleshooting.md)
3. Contact support at support@your-organization.com

## Next Steps

After installation, you can:

1. [Configure the platform](../usage/configuration.md)
2. [Upload your first documents](../usage/document-upload.md)
3. [Train your first model](../usage/model-training.md)
4. [Deploy your first agent](../usage/agent-deployment.md)
