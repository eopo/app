from flask import request, Response
from app.build_info import SHA1, VERSION
from app.config import METRICS_API_KEY
from app.monitor.base import monitor_bp
from app.prometheus_metrics import generate_metrics_response


@monitor_bp.route("/git")
def git_sha1():
    return SHA1


@monitor_bp.route("/version")
def version():
    return VERSION


@monitor_bp.route("/live")
def live():
    return "live"


@monitor_bp.route("/metrics")
def metrics():
    """
    Prometheus metrics endpoint with API key authentication
    Returns metrics in Prometheus format
    """
    # Check API key if configured
    if METRICS_API_KEY:
        provided_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not provided_key or provided_key != METRICS_API_KEY:
            return Response("Unauthorized", status=401)
    
    return generate_metrics_response()


@monitor_bp.route("/metrics/test")
def metrics_test():
    """
    Test endpoint to manually increment metrics for debugging
    """
    from app.prometheus_metrics import (
        email_forwards_total,
        email_replies_total,
        active_users_total,
        aliases_total,
        PROMETHEUS_AVAILABLE,
    )
    
    if not PROMETHEUS_AVAILABLE:
        return Response("Prometheus not available", status=503)
    
    # Test increment counters
    email_forwards_total.inc()
    email_replies_total.inc()
    
    # Test set gauges
    active_users_total.set(10)
    aliases_total.set(25)
    
    return Response("Metrics updated! Check /metrics endpoint", status=200)


@monitor_bp.route("/exception")
def test_exception():
    raise Exception("to make sure sentry works")
    return "never reach here"
