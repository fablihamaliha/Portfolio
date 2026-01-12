// Live Monitoring Dashboard JavaScript

// Chart instances
let requestRateChart = null;
let responseTimeChart = null;
let geoChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    fetchAndUpdateMetrics();

    // Auto-refresh every 30 seconds
    setInterval(fetchAndUpdateMetrics, 30000);
});

// Initialize Chart.js charts
function initializeCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    // Request Rate Chart
    const reqRateCtx = document.getElementById('requestRateChart').getContext('2d');
    requestRateChart = new Chart(reqRateCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Requests per Second'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });

    // Response Time Chart
    const respTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
    responseTimeChart = new Chart(respTimeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Response Time (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });

    // Geographic Chart
    const geoCtx = document.getElementById('geoChart').getContext('2d');
    geoChart = new Chart(geoCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Requests',
                data: [],
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        },
        options: {
            ...commonOptions,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Requests'
                    }
                }
            }
        }
    });
}

// Fetch and update all metrics
async function fetchAndUpdateMetrics() {
    try {
        updateStatus('Fetching data...', true);

        // Fetch live metrics
        const liveResponse = await fetch('/api/metrics/live');
        const liveData = await liveResponse.json();

        if (liveData.status === 'success') {
            updateQuickStats(liveData.data);
            updateAppStatus(liveData.data);
            updateStatus('Live', true);
        } else {
            updateStatus('Error fetching data', false);
        }

        // Fetch time-series data
        const timeseriesResponse = await fetch('/api/metrics/timeseries');
        const timeseriesData = await timeseriesResponse.json();

        if (timeseriesData.status === 'success') {
            updateCharts(timeseriesData.data);
        }

        // Fetch geographic data
        const geoResponse = await fetch('/api/metrics/geographic');
        const geoData = await geoResponse.json();

        if (geoData.status === 'success') {
            updateGeoChart(geoData.data);
        }

        // Fetch system metrics
        const systemResponse = await fetch('/api/metrics/system');
        const systemData = await systemResponse.json();

        if (systemData.status === 'success') {
            updateSystemMetrics(systemData.data);
        }

        // Update last update time
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

    } catch (error) {
        console.error('Error fetching metrics:', error);
        updateStatus('Connection error', false);
    }
}

// Update quick stats cards
function updateQuickStats(data) {
    // Total request rate
    const totalReqRate = data.request_rate.reduce((sum, app) => sum + app.value, 0);
    document.getElementById('totalRequestRate').textContent = totalReqRate.toFixed(2);

    // Average response time
    const avgRespTime = data.response_time_p95.reduce((sum, app) => sum + app.value, 0) /
                        (data.response_time_p95.length || 1);
    document.getElementById('avgResponseTime').textContent = avgRespTime.toFixed(0);

    // Success rate (100 - error rate)
    const avgErrorRate = data.error_rate.reduce((sum, app) => sum + app.value, 0) /
                         (data.error_rate.length || 1);
    const successRate = (100 - avgErrorRate).toFixed(2);
    document.getElementById('successRate').textContent = successRate;

    // Total requests 24h
    const total24h = data.total_requests_24h.reduce((sum, app) => sum + app.value, 0);
    document.getElementById('totalRequests24h').textContent = total24h.toLocaleString();
}

// Update app status cards
function updateAppStatus(data) {
    const appStatusGrid = document.getElementById('appStatusGrid');
    appStatusGrid.innerHTML = '';

    // Create a map of apps with their metrics
    const apps = {};

    // Gather all metrics by app
    data.uptime.forEach(item => {
        const appName = item.app || item.job.replace('_app', '');
        if (!apps[appName]) {
            apps[appName] = {
                name: appName,
                status: item.status
            };
        }
    });

    data.request_rate.forEach(item => {
        if (apps[item.app]) {
            apps[item.app].reqRate = item.value.toFixed(2);
        }
    });

    data.response_time_p95.forEach(item => {
        if (apps[item.app]) {
            apps[item.app].respTime = item.value.toFixed(0);
        }
    });

    data.error_rate.forEach(item => {
        if (apps[item.app]) {
            apps[item.app].errorRate = item.value.toFixed(2);
        }
    });

    data.total_requests_24h.forEach(item => {
        if (apps[item.app]) {
            apps[item.app].total24h = item.value.toLocaleString();
        }
    });

    // Create cards for each app
    Object.values(apps).forEach(app => {
        const card = document.createElement('div');
        card.className = `app-status-card ${app.status === 'down' ? 'down' : ''}`;

        const displayName = app.name === 'skincares' ? 'PRA (skincares.work)' :
                           app.name === 'portfolio' ? 'Portfolio (fablihamaliha.us)' :
                           app.name;

        card.innerHTML = `
            <h3>${displayName}</h3>
            <span class="app-status-badge ${app.status === 'down' ? 'down' : ''}">${app.status.toUpperCase()}</span>
            ${app.reqRate ? `
                <div class="app-metric">
                    <span class="app-metric-label">Request Rate</span>
                    <span class="app-metric-value">${app.reqRate} req/s</span>
                </div>
            ` : ''}
            ${app.respTime ? `
                <div class="app-metric">
                    <span class="app-metric-label">Response Time (p95)</span>
                    <span class="app-metric-value">${app.respTime} ms</span>
                </div>
            ` : ''}
            ${app.errorRate ? `
                <div class="app-metric">
                    <span class="app-metric-label">Error Rate</span>
                    <span class="app-metric-value">${app.errorRate}%</span>
                </div>
            ` : ''}
            ${app.total24h ? `
                <div class="app-metric">
                    <span class="app-metric-label">Total Requests (24h)</span>
                    <span class="app-metric-value">${app.total24h}</span>
                </div>
            ` : ''}
        `;

        appStatusGrid.appendChild(card);
    });
}

// Update time-series charts
function updateCharts(data) {
    // Update Request Rate Chart
    if (data.request_rate_series && data.request_rate_series.length > 0) {
        const datasets = data.request_rate_series.map((series, index) => {
            const appName = series.metric.app;
            const colors = [
                { bg: 'rgba(102, 126, 234, 0.2)', border: 'rgba(102, 126, 234, 1)' },
                { bg: 'rgba(118, 75, 162, 0.2)', border: 'rgba(118, 75, 162, 1)' }
            ];
            const color = colors[index % colors.length];

            return {
                label: appName,
                data: series.values.map(v => ({ x: new Date(v[0] * 1000), y: parseFloat(v[1]) })),
                backgroundColor: color.bg,
                borderColor: color.border,
                borderWidth: 2,
                tension: 0.4,
                fill: true
            };
        });

        requestRateChart.data.datasets = datasets;
        requestRateChart.update();
    }

    // Update Response Time Chart
    if (data.response_time_series && data.response_time_series.length > 0) {
        const datasets = data.response_time_series.map((series, index) => {
            const appName = series.metric.app;
            const colors = [
                { bg: 'rgba(72, 187, 120, 0.2)', border: 'rgba(72, 187, 120, 1)' },
                { bg: 'rgba(245, 101, 101, 0.2)', border: 'rgba(245, 101, 101, 1)' }
            ];
            const color = colors[index % colors.length];

            return {
                label: appName,
                data: series.values.map(v => ({ x: new Date(v[0] * 1000), y: parseFloat(v[1]) })),
                backgroundColor: color.bg,
                borderColor: color.border,
                borderWidth: 2,
                tension: 0.4,
                fill: true
            };
        });

        responseTimeChart.data.datasets = datasets;
        responseTimeChart.update();
    }
}

// Update geographic chart
function updateGeoChart(data) {
    if (data && data.length > 0) {
        const labels = data.map(item => item.country);
        const values = data.map(item => item.requests);

        geoChart.data.labels = labels;
        geoChart.data.datasets[0].data = values;
        geoChart.update();
    }
}

// Update system metrics
function updateSystemMetrics(data) {
    updateProgressCircle('cpu', data.cpu_usage);
    updateProgressCircle('memory', data.memory_usage);
    updateProgressCircle('disk', data.disk_usage);
}

// Update progress circle
function updateProgressCircle(type, value) {
    const circle = document.getElementById(`${type}Circle`);
    const valueSpan = document.getElementById(`${type}Value`);

    const percentage = Math.round(value);
    const degrees = (percentage / 100) * 360;

    // Color based on percentage
    let color = '#48bb78'; // Green
    if (percentage > 70) color = '#ed8936'; // Orange
    if (percentage > 90) color = '#f56565'; // Red

    circle.style.background = `conic-gradient(${color} ${degrees}deg, #e2e8f0 ${degrees}deg)`;
    valueSpan.textContent = `${percentage}%`;
}

// Update status indicator
function updateStatus(text, isConnected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusText.textContent = text;

    if (isConnected) {
        statusDot.classList.remove('error');
    } else {
        statusDot.classList.add('error');
    }
}
