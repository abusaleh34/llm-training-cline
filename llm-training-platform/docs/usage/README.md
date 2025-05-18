# LLM Training Platform Usage Guide

This guide provides instructions for using the LLM Training Platform.

## Overview

The LLM Training Platform allows you to:

1. Upload and process documents
2. Structure and organize extracted text
3. Train models on your organization's data
4. Deploy interactive AI agents
5. Manage users and access control

## Getting Started

### Logging In

1. Access the Admin Dashboard at `http://your-platform-url`
2. Enter your username and password
3. Click "Login"

### Dashboard Overview

The dashboard provides an overview of:

- Recent document uploads
- Processing status
- Training jobs
- Deployed agents
- System health

## Document Management

### Uploading Documents

1. Navigate to "Documents" > "Upload"
2. Click "Choose Files" or drag and drop files
3. Select document type (optional)
4. Select language (default: Arabic)
5. Click "Upload"

Supported file formats:
- PDF (searchable and scanned)
- DOCX
- TXT

### Monitoring Processing Status

1. Navigate to "Documents" > "Status"
2. View the status of each document:
   - Uploaded: Document has been uploaded but not processed
   - Processing: Document is being processed
   - Processed: Document has been successfully processed
   - Error: An error occurred during processing

### Viewing Processed Documents

1. Navigate to "Documents" > "Library"
2. Click on a document to view:
   - Original document
   - Extracted text
   - Processing metadata
   - OCR confidence scores (for scanned documents)

### Managing Documents

1. Navigate to "Documents" > "Library"
2. Select one or more documents
3. Use the action menu to:
   - Delete documents
   - Reprocess documents
   - Export documents
   - Add to dataset

## Data Structuring

### Creating Datasets

1. Navigate to "Data" > "Datasets"
2. Click "New Dataset"
3. Enter dataset name and description
4. Select documents to include
5. Click "Create"

### Configuring Text Chunking

1. Navigate to "Data" > "Datasets" > [Your Dataset]
2. Click "Configure Chunking"
3. Set chunking parameters:
   - Chunk size (tokens or characters)
   - Overlap percentage
   - Chunk method (sentence, paragraph, fixed size)
4. Click "Apply"

### Generating Embeddings

1. Navigate to "Data" > "Datasets" > [Your Dataset]
2. Click "Generate Embeddings"
3. Select embedding model
4. Click "Start"

### Exploring Vector Space

1. Navigate to "Data" > "Datasets" > [Your Dataset] > "Explore"
2. Use the visualization tools to:
   - View document clusters
   - Identify similar documents
   - Search for related content

## Model Training

### Creating a Training Job

1. Navigate to "Models" > "Training"
2. Click "New Training Job"
3. Configure training parameters:
   - Base model
   - Dataset
   - Training method (fine-tuning, PEFT, etc.)
   - Hyperparameters
4. Click "Start Training"

### Monitoring Training Progress

1. Navigate to "Models" > "Training" > [Your Job]
2. View training metrics:
   - Loss curves
   - Evaluation metrics
   - Resource usage
   - Estimated completion time

### Evaluating Models

1. Navigate to "Models" > "Evaluation"
2. Select a trained model
3. Configure evaluation parameters:
   - Test dataset
   - Evaluation metrics
   - Comparison models (optional)
4. Click "Start Evaluation"
5. View evaluation results:
   - Accuracy metrics
   - Performance comparison
   - Sample outputs

## Agent Deployment

### Creating an Agent

1. Navigate to "Agents" > "Deploy"
2. Click "New Agent"
3. Configure agent parameters:
   - Name and description
   - Model selection
   - Vector database connection
   - Response settings
   - Access control
4. Click "Deploy"

### Testing Agents

1. Navigate to "Agents" > "Manage" > [Your Agent] > "Test"
2. Enter test queries
3. View agent responses
4. Adjust parameters as needed

### Publishing Agents

1. Navigate to "Agents" > "Manage" > [Your Agent]
2. Click "Publish"
3. Configure access settings:
   - Public or private
   - User access list
   - API access
4. Click "Confirm"

### Monitoring Agent Usage

1. Navigate to "Agents" > "Analytics"
2. Select an agent
3. View usage metrics:
   - Query volume
   - Response times
   - User satisfaction
   - Error rates

## User Management

### Creating Users

1. Navigate to "Admin" > "Users"
2. Click "New User"
3. Enter user details:
   - Username
   - Email
   - Full name
   - Role (Admin, Manager, User)
4. Click "Create"
5. The system will send an invitation email to the user

### Managing Roles and Permissions

1. Navigate to "Admin" > "Roles"
2. Select a role to modify
3. Configure permissions:
   - Document management
   - Dataset access
   - Model training
   - Agent deployment
   - User management
4. Click "Save"

### API Key Management

1. Navigate to "Admin" > "API Keys"
2. Click "New API Key"
3. Configure key parameters:
   - Name and description
   - Permissions
   - Expiration date
4. Click "Generate"
5. Copy the API key (it will only be shown once)

## Advanced Features

### Custom Preprocessing

1. Navigate to "Settings" > "Preprocessing"
2. Configure preprocessing parameters:
   - OCR settings
   - Image preprocessing
   - Text normalization
   - Language-specific settings
3. Click "Save"

### Integration with External Systems

1. Navigate to "Settings" > "Integrations"
2. Configure integrations:
   - Document management systems
   - Knowledge bases
   - External APIs
   - Authentication providers
3. Click "Connect"

### Backup and Restore

1. Navigate to "Admin" > "Backup"
2. Configure backup settings:
   - Backup frequency
   - Retention policy
   - Storage location
3. Click "Save"
4. To restore from a backup:
   - Navigate to "Admin" > "Restore"
   - Select a backup
   - Click "Restore"

## API Usage

The platform provides a comprehensive API for programmatic access.

### Authentication

```bash
curl -X POST "http://your-platform-url/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Uploading Documents

```bash
curl -X POST "http://your-platform-url/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "document_type=contract" \
  -F "language=ar"
```

### Querying Agents

```bash
curl -X POST "http://your-platform-url/api/v1/agents/YOUR_AGENT_ID/query" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key terms in the contract?", "context": {}}'
```

For more API documentation, visit the Swagger UI at `http://your-platform-url/api/v1/docs`.

## Best Practices

### Document Preparation

- Ensure documents are properly scanned and oriented
- Use high-resolution scans for better OCR results
- Remove watermarks and unnecessary elements
- Split large documents into smaller files for better processing

### Dataset Creation

- Create focused datasets for specific domains
- Include diverse document types for better coverage
- Balance the dataset to avoid bias
- Regularly update datasets with new documents

### Model Training

- Start with smaller models for faster iteration
- Use parameter-efficient fine-tuning for large models
- Monitor training to avoid overfitting
- Evaluate models on diverse test sets

### Agent Deployment

- Start with restricted access for testing
- Collect user feedback for improvement
- Monitor performance and usage patterns
- Regularly update models based on new data

## Troubleshooting

### Common Issues

#### Document Processing Errors

- Check file format and encoding
- Verify OCR language settings
- Check for corrupted files
- Review preprocessing settings

#### Training Failures

- Check hardware resources
- Verify dataset integrity
- Review hyperparameters
- Check for model compatibility

#### Agent Response Issues

- Verify vector database connection
- Check query formatting
- Review response settings
- Test with different queries

For more troubleshooting information, see the [Troubleshooting Guide](../maintenance/troubleshooting.md).
