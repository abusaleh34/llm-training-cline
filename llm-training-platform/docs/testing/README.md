# Testing the LLM Training Platform

This guide provides instructions for testing the LLM Training Platform.

## Prerequisites

Before testing, ensure you have the following:

- Docker and Docker Compose installed
- Git installed
- Sample documents for testing (PDF, DOCX, TXT)
- Postman or curl for API testing (optional)

## Setting Up the Test Environment

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/llm-training-platform.git
cd llm-training-platform
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file to configure your test environment. For testing purposes, you can use the default values.

### 3. Build and Start the Services

```bash
cd deployment/docker
docker-compose build
docker-compose up -d
```

This will start all the services defined in the docker-compose.yml file.

### 4. Initialize the Database

```bash
docker-compose exec api-gateway python -m src.scripts.init_db
```

### 5. Create an Admin User

```bash
docker-compose exec api-gateway python -m src.scripts.create_admin_user
```

Follow the prompts to create an admin user for testing.

## Testing the Platform

### 1. Testing the API Gateway

Verify that the API Gateway is running:

```bash
curl http://localhost:8000/
```

You should receive a JSON response with information about the platform.

### 2. Testing Authentication

Obtain an access token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

Save the access token for subsequent requests.

### 3. Testing Document Upload

Upload a document:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "document_type=contract" \
  -F "language=ar"
```

### 4. Testing Document Processing

Check the status of the uploaded document:

```bash
curl -X GET http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Testing User Management

List users (admin only):

```bash
curl -X GET http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Create a new user (admin only):

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "securepassword",
    "role": "USER",
    "is_active": true
  }'
```

### 6. Testing API Key Management

Create an API key:

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Key",
    "expires_days": 30
  }'
```

List API keys:

```bash
curl -X GET http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing with the Admin Dashboard

If you prefer a graphical interface for testing:

1. Access the Admin Dashboard at `http://localhost:3000`
2. Log in with the admin credentials you created
3. Use the dashboard to:
   - Upload and manage documents
   - Create and manage users
   - Monitor document processing
   - Create and manage API keys

## Testing with Postman

For more comprehensive API testing, you can use Postman:

1. Import the Postman collection from `docs/testing/llm-training-platform.postman_collection.json`
2. Set up an environment with the following variables:
   - `base_url`: `http://localhost:8000/api/v1`
   - `username`: Your admin username
   - `password`: Your admin password
3. Run the "Get Token" request to obtain an access token
4. Use the other requests to test various API endpoints

## Automated Testing

The platform includes automated tests that you can run:

```bash
# Run unit tests
docker-compose exec api-gateway pytest src/tests/unit

# Run integration tests
docker-compose exec api-gateway pytest src/tests/integration

# Run system tests
docker-compose exec api-gateway pytest src/tests/system
```

## Testing Specific Components

### Testing OCR Capabilities

1. Upload a scanned PDF document with Arabic text
2. Check the processing status
3. Once processed, retrieve the extracted text
4. Verify that the Arabic text has been correctly extracted and processed

### Testing Document Processing Pipeline

1. Upload documents of different formats (PDF, DOCX, TXT)
2. Monitor the processing status
3. Verify that each document is processed correctly
4. Check the extracted text and metadata

### Testing Error Handling

1. Upload an invalid document (e.g., a corrupted file)
2. Verify that the system handles the error gracefully
3. Check the error message in the document status

## Troubleshooting

### Checking Logs

If you encounter issues during testing, check the logs:

```bash
# API Gateway logs
docker-compose logs api-gateway

# Document Ingestion Service logs
docker-compose logs document-ingestion

# Database logs
docker-compose logs db
```

### Common Issues

#### Authentication Issues

- Verify that you're using the correct username and password
- Check that the JWT token hasn't expired
- Ensure you're including the token in the Authorization header

#### Document Upload Issues

- Check that the file exists and is accessible
- Verify that the file format is supported
- Ensure the file size is within limits

#### Processing Issues

- Check the document ingestion service logs for errors
- Verify that the OCR engine is properly configured
- Ensure the document is in a readable format

## Next Steps

After testing the basic functionality, you can proceed to:

1. Test the data structuring capabilities
2. Test model training with your documents
3. Test agent deployment and interaction
4. Test the platform with larger volumes of documents

For more detailed testing scenarios, refer to the specific component documentation.
