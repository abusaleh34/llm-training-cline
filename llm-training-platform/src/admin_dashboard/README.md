# Admin Dashboard Service

The Admin Dashboard service provides a web-based interface for administrators to monitor and manage the LLM Training Platform. It offers real-time insights into system resources, service health, document processing, model training, and agent deployment.

## Features

- **System Monitoring**: Real-time monitoring of CPU, memory, disk, and GPU usage
- **Service Health**: Status and health information for all platform services
- **Statistics Dashboard**: Overview of documents, models, agents, and users
- **Log Viewer**: Centralized log viewing with filtering capabilities
- **User Management**: Create, update, and manage user accounts
- **Document Management**: View and manage uploaded documents
- **Model Management**: Monitor and manage model training jobs
- **Agent Management**: Deploy, monitor, and manage AI agents

## Architecture

The Admin Dashboard service is built using:

- **FastAPI**: For the backend API
- **Jinja2 Templates**: For server-side rendering
- **Bootstrap 5**: For responsive UI components
- **Chart.js**: For data visualization
- **SQLAlchemy**: For database interactions

## API Endpoints

The service exposes the following API endpoints:

- `/api/admin/system/resources`: Get system resource usage
- `/api/admin/system/status`: Get status of all services
- `/api/admin/stats`: Get dashboard statistics
- `/api/admin/logs`: Get logs from all services
- `/api/admin/restart-service/{service_name}`: Restart a specific service
- `/api/admin/clear-cache/{cache_type}`: Clear a specific type of cache

## UI Routes

- `/`: Main dashboard interface
- `/health`: Health check endpoint

## Configuration

The service can be configured using environment variables:

- `SERVICE_NAME`: Name of the service (default: "admin_dashboard")
- `SERVICE_HOST`: Host to bind the service to (default: "0.0.0.0")
- `SERVICE_PORT`: Port to bind the service to (default: 3000)
- `DEBUG`: Enable debug mode (default: false)

## Development

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend development)
- PostgreSQL 13+

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   python main.py
   ```

3. Access the dashboard at http://localhost:3000

## Docker

The service can be run using Docker:

```bash
docker build -t llm-platform/admin-dashboard -f deployment/docker/Dockerfile.admin_dashboard .
docker run -p 3000:3000 llm-platform/admin-dashboard
```

## Security Considerations

- The Admin Dashboard should only be accessible to authenticated administrators
- In production, CORS settings should be restricted to specific origins
- All API endpoints are protected with authentication middleware
- Sensitive operations require additional authorization checks
