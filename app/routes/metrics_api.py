"""
Metrics API - Fetch live metrics from Prometheus
Provides endpoints for live monitoring data to display in portfolio
"""

import requests
from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)

metrics_api_bp = Blueprint('metrics_api', __name__)

# Prometheus URL (localhost since this runs on the Pi)
PROMETHEUS_URL = 'http://localhost:9090/api/v1/query'


def query_prometheus(query):
    """Query Prometheus and return results"""
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': query}, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Prometheus query failed: {e}")
        return None


@metrics_api_bp.route('/api/metrics/live')
def get_live_metrics():
    """
    Get live metrics for both apps (PRA and Portfolio)
    Returns: Request rate, response time, error rate, uptime
    """
    try:
        metrics = {}

        # 1. Request Rate (requests per second)
        req_rate_query = 'sum(rate(http_requests_total[5m])) by (app)'
        req_rate_data = query_prometheus(req_rate_query)
        if req_rate_data and req_rate_data.get('status') == 'success':
            metrics['request_rate'] = [
                {
                    'app': result['metric']['app'],
                    'value': float(result['value'][1])
                }
                for result in req_rate_data['data']['result']
            ]
        else:
            metrics['request_rate'] = []

        # 2. Response Time (95th percentile in milliseconds)
        resp_time_query = '''
            histogram_quantile(0.95,
              sum(rate(http_request_duration_seconds_bucket[5m])) by (app, le)
            ) * 1000
        '''
        resp_time_data = query_prometheus(resp_time_query)
        if resp_time_data and resp_time_data.get('status') == 'success':
            metrics['response_time_p95'] = [
                {
                    'app': result['metric']['app'],
                    'value': float(result['value'][1])
                }
                for result in resp_time_data['data']['result']
            ]
        else:
            metrics['response_time_p95'] = []

        # 3. Error Rate (percentage)
        error_rate_query = '''
            (sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (app) /
             sum(rate(http_requests_total[5m])) by (app)) * 100
        '''
        error_rate_data = query_prometheus(error_rate_query)
        if error_rate_data and error_rate_data.get('status') == 'success':
            metrics['error_rate'] = [
                {
                    'app': result['metric']['app'],
                    'value': float(result['value'][1])
                }
                for result in error_rate_data['data']['result']
            ]
        else:
            metrics['error_rate'] = []

        # 4. Total Requests (last 24 hours)
        total_requests_query = 'sum(increase(http_requests_total[24h])) by (app)'
        total_data = query_prometheus(total_requests_query)
        if total_data and total_data.get('status') == 'success':
            metrics['total_requests_24h'] = [
                {
                    'app': result['metric']['app'],
                    'value': int(float(result['value'][1]))
                }
                for result in total_data['data']['result']
            ]
        else:
            metrics['total_requests_24h'] = []

        # 5. Uptime (service up/down)
        uptime_query = 'up{job=~"pra_app|portfolio_app"}'
        uptime_data = query_prometheus(uptime_query)
        if uptime_data and uptime_data.get('status') == 'success':
            metrics['uptime'] = [
                {
                    'app': result['metric'].get('app', 'unknown'),
                    'job': result['metric']['job'],
                    'status': 'up' if result['value'][1] == '1' else 'down'
                }
                for result in uptime_data['data']['result']
            ]
        else:
            metrics['uptime'] = []

        return jsonify({
            'status': 'success',
            'data': metrics,
            'timestamp': req_rate_data['data'].get('resultType') if req_rate_data else None
        })

    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@metrics_api_bp.route('/api/metrics/timeseries')
def get_timeseries_metrics():
    """
    Get time-series data for charts (last 6 hours)
    Returns: Request rate and response time over time
    """
    try:
        # Use range query for time-series data
        PROMETHEUS_RANGE_URL = 'http://localhost:9090/api/v1/query_range'

        metrics = {}

        # Request rate over time (5-minute intervals)
        req_rate_params = {
            'query': 'sum(rate(http_requests_total[5m])) by (app)',
            'start': 'now-6h',
            'end': 'now',
            'step': '5m'
        }
        req_rate_data = requests.get(PROMETHEUS_RANGE_URL, params=req_rate_params, timeout=10)
        if req_rate_data.status_code == 200:
            metrics['request_rate_series'] = req_rate_data.json()['data']['result']
        else:
            metrics['request_rate_series'] = []

        # Response time over time
        resp_time_params = {
            'query': 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (app, le)) * 1000',
            'start': 'now-6h',
            'end': 'now',
            'step': '5m'
        }
        resp_time_data = requests.get(PROMETHEUS_RANGE_URL, params=resp_time_params, timeout=10)
        if resp_time_data.status_code == 200:
            metrics['response_time_series'] = resp_time_data.json()['data']['result']
        else:
            metrics['response_time_series'] = []

        return jsonify({
            'status': 'success',
            'data': metrics
        })

    except Exception as e:
        logger.error(f"Failed to fetch time-series metrics: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@metrics_api_bp.route('/api/metrics/geographic')
def get_geographic_metrics():
    """
    Get geographic distribution of traffic
    Returns: Top countries by request count
    """
    try:
        # Top 10 countries by request count (last 24h)
        geo_query = 'topk(10, sum(increase(http_requests_total[24h])) by (country))'
        geo_data = query_prometheus(geo_query)

        if geo_data and geo_data.get('status') == 'success':
            countries = [
                {
                    'country': result['metric'].get('country', 'Unknown'),
                    'requests': int(float(result['value'][1]))
                }
                for result in geo_data['data']['result']
            ]
            return jsonify({
                'status': 'success',
                'data': countries
            })
        else:
            return jsonify({
                'status': 'success',
                'data': []
            })

    except Exception as e:
        logger.error(f"Failed to fetch geographic metrics: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@metrics_api_bp.route('/api/metrics/system')
def get_system_metrics():
    """
    Get system metrics (CPU, Memory, Disk)
    Returns: Current system resource usage
    """
    try:
        metrics = {}

        # CPU usage (percentage)
        cpu_query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        cpu_data = query_prometheus(cpu_query)
        if cpu_data and cpu_data.get('status') == 'success' and cpu_data['data']['result']:
            metrics['cpu_usage'] = float(cpu_data['data']['result'][0]['value'][1])
        else:
            metrics['cpu_usage'] = 0

        # Memory usage (percentage)
        mem_query = '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))'
        mem_data = query_prometheus(mem_query)
        if mem_data and mem_data.get('status') == 'success' and mem_data['data']['result']:
            metrics['memory_usage'] = float(mem_data['data']['result'][0]['value'][1])
        else:
            metrics['memory_usage'] = 0

        # Disk usage (percentage)
        disk_query = '100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)'
        disk_data = query_prometheus(disk_query)
        if disk_data and disk_data.get('status') == 'success' and disk_data['data']['result']:
            metrics['disk_usage'] = float(disk_data['data']['result'][0]['value'][1])
        else:
            metrics['disk_usage'] = 0

        return jsonify({
            'status': 'success',
            'data': metrics
        })

    except Exception as e:
        logger.error(f"Failed to fetch system metrics: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@metrics_api_bp.route('/api/metrics/health')
def health_check():
    """Health check endpoint for the metrics API"""
    try:
        # Test Prometheus connectivity
        test_query = 'up'
        result = query_prometheus(test_query)

        if result and result.get('status') == 'success':
            return jsonify({
                'status': 'healthy',
                'prometheus': 'connected'
            })
        else:
            return jsonify({
                'status': 'degraded',
                'prometheus': 'disconnected'
            }), 503

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
