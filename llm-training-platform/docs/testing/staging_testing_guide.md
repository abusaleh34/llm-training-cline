# Step-by-Step Testing Guide for Staging Deployment

This guide provides detailed instructions on how to test the staging deployment of the LLM Training Platform. It covers both automated and manual testing approaches.

## Prerequisites

- GitHub account with access to the repository
- Docker and Docker Compose installed locally (for local testing)
- Git CLI installed
- cURL or Postman for API testing
- Web browser for UI testing

## 1. Triggering the Automated Deployment

### Option 1: Via GitHub UI

1. Navigate to the GitHub repository
2. Go to the "Actions" tab
3. Select the "Staging Deployment" workflow
4. Click "Run workflow"
5. Select the branch to deploy (usually `main` or `develop`)
6. Click "Run workflow" to start the deployment process

### Option 2: Via Git Push

1. Make a change to the codebase
2. Commit your changes:
   ```bash
   git add .
   git commit -m "Your commit message"
   ```
3. Push to a branch that triggers the workflow:
   ```bash
   git push origin main
   # or
   git push origin develop
   ```

### Option 3: Via Manual Trigger

```bash
# Using GitHub CLI
gh workflow run staging-deploy.yml -R <owner>/<repo>

# Using GitHub API
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/<owner>/<repo>/actions/workflows/staging-deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

## 2. Monitoring the Deployment Process

1. Go to the "Actions" tab in the GitHub repository
2. Find your running workflow and click on it
3. Monitor the progress of each job:
   - Prepare
   - Build
   - Test
   - Deploy
   - Cleanup
4. Check the logs for any errors or warnings
5. Wait for the deployment to complete successfully

## 3. Accessing the Staging Environment

Once the deployment is complete, you'll receive a deployment summary with:

1. The staging URL (e.g., `https://staging-abc123.llm-platform.example.com`)
2. Basic authentication credentials:
   - Username: `qa`
   - Password: `qa123`
3. API documentation URL

Access the staging environment using these credentials in your web browser.

## 4. Testing the API Gateway

### Health Check Endpoint

```bash
# Test the health check endpoint
curl -X GET https://staging-abc123.llm-platform.example.com/healthz

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-05-17T19:30:00.000Z",
#   "version": "1.0.0",
#   "environment": "staging",
#   "components": {
#     "database": "healthy"
#   }
# }
```

### API Endpoints with Authentication

```bash
# Test the API endpoints with basic auth
curl -X GET \
  -u qa:qa123 \
  https://staging-abc123.llm-platform.example.com/api/v1/documents

# Expected response: List of documents in JSON format
```

## 5. Testing Document Ingestion

### Upload a Document

1. Log in to the web interface using the provided credentials
2. Navigate to the "Documents" section
3. Click "Upload Document"
4. Select a test document (PDF, DOCX, or TXT)
5. Fill in the required metadata
6. Click "Upload"
7. Verify that the document appears in the document list
8. Check the document status changes from "Uploaded" to "Processing" to "Processed"

### API-based Document Upload

```bash
# Get an authentication token
TOKEN=$(curl -X POST \
  -u qa:qa123 \
  https://staging-abc123.llm-platform.example.com/api/v1/auth/token \
  -d '{"username":"user","password":"password"}' \
  -H "Content-Type: application/json" | jq -r '.access_token')

# Upload a document
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/test/document.pdf" \
  -F "language=en" \
  -F "document_type=contract" \
  https://staging-abc123.llm-platform.example.com/api/v1/documents/upload
```

## 6. Testing Data Structuring

1. Log in to the web interface
2. Navigate to the "Datasets" section
3. Create a new dataset from processed documents
4. Verify chunking and embedding generation
5. Test the search functionality with various queries

## 7. Testing Model Training

### RAG Testing

1. Navigate to the "Models" section
2. Create a new RAG configuration
3. Select a dataset to use
4. Configure the embedding model and retrieval parameters
5. Deploy the RAG model
6. Test the model with various queries
7. Verify that responses include citations to source documents

### Fine-tuning Testing

1. Navigate to the "Models" section
2. Create a new fine-tuning job
3. Select a base model and dataset
4. Configure training parameters
5. Start the fine-tuning job
6. Monitor the training progress
7. Test the fine-tuned model with various prompts

## 8. Testing Agent Deployment

1. Navigate to the "Agents" section
2. Create a new agent
3. Select a model (RAG or fine-tuned)
4. Configure agent parameters
5. Deploy the agent
6. Test the agent with various queries
7. Verify that the agent responds correctly and cites sources when appropriate

## 9. Testing Admin Dashboard

1. Log in as an admin user (username: `admin`, password: `password`)
2. Navigate to the "Dashboard" section
3. Verify that system metrics are displayed correctly
4. Check user management functionality
5. Test document management features
6. Verify model and agent monitoring

## 10. Security Testing

### Authentication

1. Try accessing protected endpoints without authentication
2. Test with invalid credentials
3. Verify token expiration and refresh

### Encryption

1. Upload a document and verify it's stored encrypted
2. Check database for sensitive information (should be encrypted)
3. Verify TLS/SSL is working correctly

## 11. Performance Testing

1. Upload multiple documents simultaneously
2. Process large documents and monitor resource usage
3. Test concurrent user access
4. Measure response times for various operations

## 12. Automated Testing

The CI/CD pipeline includes automated tests that run before deployment:

1. Unit tests: Test individual components in isolation
2. Integration tests: Test interactions between components
3. Health checks: Verify the deployment is functioning correctly

You can run these tests locally:

```bash
# Run unit tests
cd llm-training-platform
python -m pytest tests/unit

# Run integration tests
python -m pytest tests/integration

# Run system tests
python -m pytest tests/system
```

## 13. Cleanup

The staging environment is automatically destroyed after 72 hours. To manually clean up:

1. Go to the GitHub Actions tab
2. Find the "Cleanup Staging Environment" workflow
3. Run it manually with the deployment ID

Alternatively, you can clean up using Docker Compose:

```bash
cd llm-training-platform/deployment/docker
docker-compose -f docker-compose.staging.yml --env-file .env.staging -p staging-abc123 down -v
```

## 14. Reporting Issues

If you encounter any issues during testing:

1. Check the deployment logs in the GitHub Actions tab
2. Look at the container logs:
   ```bash
   docker-compose -f docker-compose.staging.yml --env-file .env.staging -p staging-abc123 logs [service_name]
   ```
3. Create an issue in the GitHub repository with:
   - Detailed description of the issue
   - Steps to reproduce
   - Expected vs. actual behavior
   - Deployment ID and timestamp
   - Screenshots or logs if applicable

## 15. Validating Test Results

After completing the tests, validate the results against the requirements:

1. Document ingestion works correctly for all supported file types
2. Data structuring properly chunks and indexes documents
3. Model training (both RAG and fine-tuning) produces functional models
4. Agents can be deployed and respond correctly to queries
5. Admin dashboard provides necessary monitoring and management features
6. Security measures are effective
7. The system performs adequately under load

Document your findings and share them with the development team.
