/**
 * Admin Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadDashboardData();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Hide all sections except the dashboard
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById('dashboard-section').classList.add('active');
    
    // Set active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector('.nav-link[data-section="dashboard-section"]').classList.add('active');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the section to show
            const sectionId = this.getAttribute('data-section');
            
            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show the selected section
            document.getElementById(sectionId).classList.add('active');
            
            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(navLink => {
                navLink.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', function() {
        loadDashboardData();
    });
    
    // Refresh logs button
    document.getElementById('refresh-logs').addEventListener('click', function() {
        loadLogs();
    });
    
    // Log filters
    document.getElementById('log-service-filter').addEventListener('change', function() {
        loadLogs();
    });
    
    document.getElementById('log-level-filter').addEventListener('change', function() {
        loadLogs();
    });
    
    document.getElementById('log-search').addEventListener('input', function() {
        // Debounce search input
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            loadLogs();
        }, 500);
    });
}

/**
 * Load dashboard data
 */
function loadDashboardData() {
    // Show loading indicators
    showLoading();
    
    // Load system resources
    loadSystemResources();
    
    // Load service status
    loadServiceStatus();
    
    // Load statistics
    loadStatistics();
    
    // Load recent activity
    loadRecentActivity();
    
    // Load system alerts
    loadSystemAlerts();
}

/**
 * Show loading indicators
 */
function showLoading() {
    // Add loading indicators to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('loading');
    });
}

/**
 * Load system resources
 */
function loadSystemResources() {
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        const resources = {
            cpu: {
                current: 45,
                average: 38,
                peak: 72,
                time_period_minutes: 60
            },
            memory: {
                current: 62,
                average: 58,
                peak: 75,
                time_period_minutes: 60
            },
            disk: {
                total_gb: 500,
                used_gb: 215,
                free_gb: 285,
                usage_percent: 43
            },
            gpu: {
                current: 30,
                average: 25,
                peak: 85,
                time_period_minutes: 60
            },
            timestamp: new Date().toISOString()
        };
        
        // Update UI
        updateSystemResourcesUI(resources);
    }, 500);
}

/**
 * Update system resources UI
 */
function updateSystemResourcesUI(resources) {
    // CPU usage
    const cpuUsage = document.getElementById('cpu-usage');
    cpuUsage.style.width = `${resources.cpu.current}%`;
    cpuUsage.setAttribute('aria-valuenow', resources.cpu.current);
    cpuUsage.textContent = `${resources.cpu.current}%`;
    
    // Memory usage
    const memoryUsage = document.getElementById('memory-usage');
    memoryUsage.style.width = `${resources.memory.current}%`;
    memoryUsage.setAttribute('aria-valuenow', resources.memory.current);
    memoryUsage.textContent = `${resources.memory.current}%`;
    
    // Disk usage
    const diskUsage = document.getElementById('disk-usage');
    diskUsage.style.width = `${resources.disk.usage_percent}%`;
    diskUsage.setAttribute('aria-valuenow', resources.disk.usage_percent);
    diskUsage.textContent = `${resources.disk.usage_percent}%`;
    
    // GPU usage
    const gpuUsage = document.getElementById('gpu-usage');
    if (resources.gpu) {
        gpuUsage.style.width = `${resources.gpu.current}%`;
        gpuUsage.setAttribute('aria-valuenow', resources.gpu.current);
        gpuUsage.textContent = `${resources.gpu.current}%`;
    } else {
        gpuUsage.style.width = '0%';
        gpuUsage.setAttribute('aria-valuenow', 0);
        gpuUsage.textContent = 'N/A';
    }
}

/**
 * Load service status
 */
function loadServiceStatus() {
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        const status = {
            services: [
                {
                    name: 'api-gateway',
                    status: 'running',
                    uptime: '3d 12h 45m',
                    health: 'healthy',
                    version: '1.0.0',
                    last_restart: '2025-05-14T06:15:00Z'
                },
                {
                    name: 'document-ingestion',
                    status: 'running',
                    uptime: '3d 12h 45m',
                    health: 'healthy',
                    version: '1.0.0',
                    last_restart: '2025-05-14T06:15:00Z'
                },
                {
                    name: 'data-structuring',
                    status: 'warning',
                    uptime: '1d 5h 30m',
                    health: 'warning',
                    version: '1.0.0',
                    last_restart: '2025-05-16T13:30:00Z'
                },
                {
                    name: 'model-training',
                    status: 'running',
                    uptime: '3d 12h 45m',
                    health: 'healthy',
                    version: '1.0.0',
                    last_restart: '2025-05-14T06:15:00Z'
                },
                {
                    name: 'agent-deployment',
                    status: 'running',
                    uptime: '3d 12h 45m',
                    health: 'healthy',
                    version: '1.0.0',
                    last_restart: '2025-05-14T06:15:00Z'
                },
                {
                    name: 'admin-dashboard',
                    status: 'running',
                    uptime: '3d 12h 45m',
                    health: 'healthy',
                    version: '1.0.0',
                    last_restart: '2025-05-14T06:15:00Z'
                }
            ],
            overall_health: 'degraded',
            timestamp: new Date().toISOString()
        };
        
        // Update UI
        updateServiceStatusUI(status);
    }, 700);
}

/**
 * Update service status UI
 */
function updateServiceStatusUI(status) {
    const tableBody = document.getElementById('service-status-table');
    tableBody.innerHTML = '';
    
    status.services.forEach(service => {
        const row = document.createElement('tr');
        
        // Status class
        let statusClass = '';
        switch (service.health) {
            case 'healthy':
                statusClass = 'status-running';
                break;
            case 'warning':
                statusClass = 'status-warning';
                break;
            case 'unhealthy':
                statusClass = 'status-error';
                break;
            default:
                statusClass = 'status-stopped';
        }
        
        row.innerHTML = `
            <td>${service.name}</td>
            <td><span class="status-indicator ${statusClass}"></span>${service.status}</td>
            <td>${service.health}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Load statistics
 */
function loadStatistics() {
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        const stats = {
            document_stats: {
                total_documents: 1250,
                documents_by_type: {
                    pdf: 750,
                    docx: 350,
                    txt: 150
                },
                total_pages: 8750,
                total_size_mb: 2345.67,
                documents_processed_24h: 45,
                processing_success_rate: 98.5
            },
            model_stats: {
                total_models: 25,
                models_by_type: {
                    fine_tuned: 15,
                    rag: 10
                },
                fine_tuned_models: 15,
                total_training_hours: 345.5,
                average_training_time: 23.03,
                training_jobs_24h: 3
            },
            agent_stats: {
                total_agents: 18,
                active_agents: 8,
                agents_by_type: {
                    fine_tuned: 10,
                    rag: 8
                },
                total_interactions: 12500,
                interactions_24h: 350,
                average_response_time_ms: 450.75
            },
            user_stats: {
                total_users: 75,
                active_users: 45,
                users_by_role: {
                    admin: 5,
                    manager: 15,
                    user: 55
                },
                logins_24h: 35,
                average_session_duration: 45.5
            },
            last_updated: new Date().toISOString()
        };
        
        // Update UI
        updateStatisticsUI(stats);
    }, 600);
}

/**
 * Update statistics UI
 */
function updateStatisticsUI(stats) {
    // Update document stats
    document.getElementById('total-documents').textContent = stats.document_stats.total_documents;
    
    // Update model stats
    document.getElementById('total-models').textContent = stats.model_stats.total_models;
    
    // Update agent stats
    document.getElementById('total-agents').textContent = stats.agent_stats.total_agents;
    
    // Update user stats
    document.getElementById('total-users').textContent = stats.user_stats.total_users;
}

/**
 * Load recent activity
 */
function loadRecentActivity() {
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        const activities = [
            {
                type: 'document',
                action: 'upload',
                user: 'ahmed',
                timestamp: '2025-05-17T17:25:00Z',
                details: 'Uploaded contract.pdf (2.5 MB)'
            },
            {
                type: 'model',
                action: 'train',
                user: 'sara',
                timestamp: '2025-05-17T16:45:00Z',
                details: 'Started training model "Legal-Assistant-v2"'
            },
            {
                type: 'agent',
                action: 'deploy',
                user: 'mohammed',
                timestamp: '2025-05-17T15:30:00Z',
                details: 'Deployed agent "Contract-Analyzer"'
            },
            {
                type: 'user',
                action: 'create',
                user: 'admin',
                timestamp: '2025-05-17T14:15:00Z',
                details: 'Created user "khalid"'
            },
            {
                type: 'document',
                action: 'process',
                user: 'system',
                timestamp: '2025-05-17T13:45:00Z',
                details: 'Processed 15 documents'
            }
        ];
        
        // Update UI
        updateRecentActivityUI(activities);
    }, 800);
}

/**
 * Update recent activity UI
 */
function updateRecentActivityUI(activities) {
    const activityContainer = document.getElementById('recent-activity');
    activityContainer.innerHTML = '';
    
    activities.forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item d-flex align-items-center';
        
        // Format timestamp
        const timestamp = new Date(activity.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        // Icon class
        const iconClass = `activity-icon activity-icon-${activity.type}`;
        
        activityItem.innerHTML = `
            <div class="${iconClass}">
                <i class="bi bi-${getActivityIcon(activity.type, activity.action)}"></i>
            </div>
            <div>
                <div>${activity.details}</div>
                <div class="activity-time">
                    <i class="bi bi-person"></i> ${activity.user} · ${timeAgo}
                </div>
            </div>
        `;
        
        activityContainer.appendChild(activityItem);
    });
}

/**
 * Get activity icon
 */
function getActivityIcon(type, action) {
    switch (type) {
        case 'document':
            return action === 'upload' ? 'file-earmark-arrow-up' : 'file-earmark-text';
        case 'model':
            return 'cpu';
        case 'agent':
            return 'robot';
        case 'user':
            return 'person';
        default:
            return 'activity';
    }
}

/**
 * Load system alerts
 */
function loadSystemAlerts() {
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        const alerts = [
            {
                type: 'warning',
                message: 'High memory usage detected (75%)',
                timestamp: '2025-05-17T17:20:00Z'
            },
            {
                type: 'info',
                message: 'Model training "Legal-Assistant-v2" completed successfully',
                timestamp: '2025-05-17T16:45:00Z'
            },
            {
                type: 'danger',
                message: 'Data structuring service experiencing high latency',
                timestamp: '2025-05-17T15:30:00Z'
            },
            {
                type: 'success',
                message: 'System backup completed successfully',
                timestamp: '2025-05-17T12:00:00Z'
            }
        ];
        
        // Update UI
        updateSystemAlertsUI(alerts);
    }, 900);
}

/**
 * Update system alerts UI
 */
function updateSystemAlertsUI(alerts) {
    const alertsContainer = document.getElementById('system-alerts');
    alertsContainer.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item alert-item-${alert.type}`;
        
        // Format timestamp
        const timestamp = new Date(alert.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        alertItem.innerHTML = `
            <div class="d-flex justify-content-between">
                <strong>${alert.message}</strong>
                <small>${timeAgo}</small>
            </div>
        `;
        
        alertsContainer.appendChild(alertItem);
    });
}

/**
 * Load logs
 */
function loadLogs() {
    // Get filter values
    const serviceFilter = document.getElementById('log-service-filter').value;
    const levelFilter = document.getElementById('log-level-filter').value;
    const searchFilter = document.getElementById('log-search').value;
    
    // In a real implementation, this would fetch data from the API
    // For now, we'll just use mock data
    
    // Simulate API call delay
    setTimeout(() => {
        // Mock data
        let logs = [
            {
                timestamp: '2025-05-17T17:25:00Z',
                service: 'document-ingestion',
                level: 'INFO',
                message: 'Processing document: contract.pdf'
            },
            {
                timestamp: '2025-05-17T17:24:30Z',
                service: 'document-ingestion',
                level: 'INFO',
                message: 'Document uploaded: contract.pdf'
            },
            {
                timestamp: '2025-05-17T17:20:00Z',
                service: 'admin-dashboard',
                level: 'WARNING',
                message: 'High memory usage detected (75%)'
            },
            {
                timestamp: '2025-05-17T17:15:00Z',
                service: 'model-training',
                level: 'INFO',
                message: 'Training model: Legal-Assistant-v2'
            },
            {
                timestamp: '2025-05-17T17:10:00Z',
                service: 'agent-deployment',
                level: 'INFO',
                message: 'Agent deployed: Contract-Analyzer'
            },
            {
                timestamp: '2025-05-17T17:05:00Z',
                service: 'data-structuring',
                level: 'ERROR',
                message: 'Failed to connect to vector database'
            },
            {
                timestamp: '2025-05-17T17:00:00Z',
                service: 'api-gateway',
                level: 'INFO',
                message: 'User authenticated: ahmed'
            },
            {
                timestamp: '2025-05-17T16:55:00Z',
                service: 'api-gateway',
                level: 'DEBUG',
                message: 'Request received: GET /api/documents'
            },
            {
                timestamp: '2025-05-17T16:50:00Z',
                service: 'document-ingestion',
                level: 'INFO',
                message: 'Document processed successfully: report.docx'
            },
            {
                timestamp: '2025-05-17T16:45:00Z',
                service: 'model-training',
                level: 'INFO',
                message: 'Model training completed: Legal-Assistant-v1'
            }
        ];
        
        // Apply filters
        if (serviceFilter) {
            logs = logs.filter(log => log.service === serviceFilter);
        }
        
        if (levelFilter) {
            logs = logs.filter(log => log.level === levelFilter);
        }
        
        if (searchFilter) {
            const searchLower = searchFilter.toLowerCase();
            logs = logs.filter(log => 
                log.message.toLowerCase().includes(searchLower) || 
                log.service.toLowerCase().includes(searchLower)
            );
        }
        
        // Update UI
        updateLogsUI(logs);
    }, 500);
}

/**
 * Update logs UI
 */
function updateLogsUI(logs) {
    const logsTable = document.getElementById('logs-table');
    logsTable.innerHTML = '';
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        // Format timestamp
        const timestamp = new Date(log.timestamp);
        const formattedTime = timestamp.toLocaleString();
        
        // Level class
        let levelClass = '';
        switch (log.level) {
            case 'DEBUG':
                levelClass = 'log-level-debug';
                break;
            case 'INFO':
                levelClass = 'log-level-info';
                break;
            case 'WARNING':
                levelClass = 'log-level-warning';
                break;
            case 'ERROR':
                levelClass = 'log-level-error';
                break;
            case 'CRITICAL':
                levelClass = 'log-level-critical';
                break;
        }
        
        row.innerHTML = `
            <td>${formattedTime}</td>
            <td>${log.service}</td>
            <td><span class="log-level ${levelClass}">${log.level}</span></td>
            <td>${log.message}</td>
        `;
        
        logsTable.appendChild(row);
    });
}

/**
 * Get time ago string
 */
function getTimeAgo(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    
    // Convert to seconds
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) {
        return `${seconds} seconds ago`;
    }
    
    // Convert to minutes
    const minutes = Math.floor(seconds / 60);
    
    if (minutes < 60) {
        return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    }
    
    // Convert to hours
    const hours = Math.floor(minutes / 60);
    
    if (hours < 24) {
        return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
    
    // Convert to days
    const days = Math.floor(hours / 24);
    
    return `${days} day${days === 1 ? '' : 's'} ago`;
}
