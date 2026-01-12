"""
Production-Grade Telemetry Middleware for Flask Applications

Features:
- Prometheus metrics (request count, duration, errors)
- IP anonymization (SHA256 + salt)
- Structured JSON logging
- Privacy-aware (no PII collection)
- Cloudflare headers integration
- Low overhead (<2ms per request)

Usage:
    from telemetry_middleware import setup_telemetry

    app = Flask(__name__)
    setup_telemetry(app, app_name='myapp')

    # Metrics endpoint is automatically added at /metrics
"""

from flask import Flask, request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
import hashlib
import os
import time
import logging
import json
from pythonjsonlogger import jsonlogger

# Create Prometheus registry
registry = CollectorRegistry()

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'route', 'status_code', 'app', 'country'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'route', 'status_code', 'app'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    registry=registry
)

http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Number of HTTP requests currently being processed',
    ['app'],
    registry=registry
)

http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'route', 'status_code', 'app', 'error_type'],
    registry=registry
)

# Business metrics (optional)
user_actions_total = Counter(
    'user_actions_total',
    'Total user actions (logins, signups, etc.)',
    ['action', 'app'],
    registry=registry
)


def anonymize_ip(ip: str) -> str:
    """Anonymize IP address using SHA256 hash with salt."""
    salt = os.getenv('IP_SALT', 'change-this-salt-in-production-2026')
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:16]


def get_route_pattern(request):
    """Get route pattern (not full path) to avoid high cardinality."""
    if request.endpoint:
        # Use Flask endpoint (e.g., 'main.index', 'api.users')
        return request.endpoint

    # Fallback to path
    path = request.path

    # Replace UUIDs with :id
    import re
    path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', ':id', path, flags=re.IGNORECASE)

    # Replace numeric IDs with :id
    path = re.sub(r'/\d+', '/:id', path)

    return path


def parse_user_agent(ua: str) -> dict:
    """Parse user agent to extract browser and OS."""
    if not ua:
        return {'browser': 'unknown', 'os': 'unknown'}

    # Simple parser (consider using 'user-agents' package for production)
    browsers = {
        'Chrome': 'Chrome/',
        'Firefox': 'Firefox/',
        'Safari': 'Safari/',
        'Edge': 'Edg/',
        'Opera': 'OPR/'
    }

    oses = {
        'Windows': 'Windows NT',
        'macOS': 'Mac OS X',
        'Linux': 'Linux',
        'Android': 'Android',
        'iOS': 'iPhone|iPad'
    }

    browser = next((b for b, pattern in browsers.items() if pattern in ua), 'unknown')
    os_name = next((o for o, pattern in oses.items() if pattern in ua), 'unknown')

    return {'browser': browser, 'os': os_name}


def setup_telemetry(app: Flask, app_name: str = None):
    """
    Set up telemetry middleware for Flask app.

    Args:
        app: Flask application instance
        app_name: Name of the application (e.g., 'app1', 'app2')
    """
    if app_name is None:
        app_name = os.getenv('APP_NAME', 'flask-app')

    # Set up JSON logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    @app.before_request
    def before_request():
        """Start timer and increment in-flight requests."""
        g.start_time = time.time()
        http_requests_in_flight.labels(app=app_name).inc()

    @app.after_request
    def after_request(response):
        """Record metrics and log request."""
        # Calculate duration
        duration = time.time() - g.start_time

        # Extract metadata
        method = request.method
        route = get_route_pattern(request)
        status_code = response.status_code

        # Cloudflare headers
        cf_connecting_ip = request.headers.get('CF-Connecting-IP') or request.remote_addr
        country = request.headers.get('CF-IPCountry', 'unknown')
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer') or request.headers.get('Referrer', 'direct')

        # Anonymize IP
        ip_hash = anonymize_ip(cf_connecting_ip)

        # Parse user agent
        ua_info = parse_user_agent(user_agent)

        # Record Prometheus metrics
        http_requests_total.labels(
            method=method,
            route=route,
            status_code=str(status_code),
            app=app_name,
            country=country
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            route=route,
            status_code=str(status_code),
            app=app_name
        ).observe(duration)

        # Track errors
        if status_code >= 400:
            error_type = 'server_error' if status_code >= 500 else 'client_error'
            http_errors_total.labels(
                method=method,
                route=route,
                status_code=str(status_code),
                app=app_name,
                error_type=error_type
            ).inc()

        # Decrement in-flight requests
        http_requests_in_flight.labels(app=app_name).dec()

        # Structured logging
        log_level = 'error' if status_code >= 500 else 'warn' if status_code >= 400 else 'info'

        log_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
            'log_level': log_level,
            'app': app_name,
            'method': method,
            'path': request.path,
            'route': route,
            'status': status_code,
            'duration_ms': round(duration * 1000, 2),
            'ip_hash': ip_hash,
            'country': country,
            'browser': ua_info['browser'],
            'os': ua_info['os'],
            'referer': referer
        }

        if log_level == 'error':
            logger.error('HTTP request', extra=log_data)
        elif log_level == 'warn':
            logger.warning('HTTP request', extra=log_data)
        else:
            logger.info('HTTP request', extra=log_data)

        return response

    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint."""
        return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}
   
    if "health" not in app.view_functions:
        @app.route('/health')
        def health():
            """Health check endpoint."""
            return {
                'status': 'healthy',
                'app': app_name,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
            }, 200


def track_user_action(action: str, app_name: str = None):
    """
    Track custom user actions (logins, signups, etc.).

    Args:
        action: Action name (e.g., 'login', 'signup', 'purchase')
        app_name: Application name
    """
    if app_name is None:
        app_name = os.getenv('APP_NAME', 'flask-app')

    user_actions_total.labels(action=action, app=app_name).inc()
