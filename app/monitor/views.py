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
    
    # Update gauges on-demand before returning metrics
    _update_user_and_alias_metrics()
    _update_postfix_metrics()
    
    return generate_metrics_response()


def _update_postfix_metrics():
    """Update Postfix queue metrics on-demand"""
    from app.prometheus_metrics import postfix_queue_size, PROMETHEUS_AVAILABLE
    import os
    
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        # Check if postfix directories exist
        postfix_spool = "/var/spool/postfix"
        if not os.path.exists(postfix_spool):
            return
        
        # Count files in postfix queues
        incoming = _count_files(f"{postfix_spool}/incoming")
        active = _count_files(f"{postfix_spool}/active")
        deferred = _count_files(f"{postfix_spool}/deferred")
        
        postfix_queue_size.labels(queue_type="incoming").set(incoming)
        postfix_queue_size.labels(queue_type="active").set(active)
        postfix_queue_size.labels(queue_type="deferred").set(deferred)
    except Exception:
        # Silently fail if postfix directories don't exist or aren't readable
        pass


def _count_files(directory):
    """Count files in directory and subdirectories"""
    import os
    if not os.path.exists(directory):
        return 0
    try:
        return sum(len(files) for _, _, files in os.walk(directory))
    except Exception:
        return 0


def _update_user_and_alias_metrics():
    """Update gauge metrics for active users and total aliases on-demand"""
    from app.prometheus_metrics import (
        active_users_total,
        aliases_total,
        PROMETHEUS_AVAILABLE,
    )
    from app.models import User, Alias
    from app.db import Session
    
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        # Count active users (not disabled)
        active_users = Session.query(User).filter(
            User.disabled == False,  # noqa: E712
        ).count()
        
        # Count total aliases (not deleted)
        total_aliases = Session.query(Alias).filter(
            Alias.delete_on == None,  # noqa: E711
        ).count()
        
        # Update Prometheus gauges
        active_users_total.set(active_users)
        aliases_total.set(total_aliases)
    except Exception:
        # Silently fail if database query fails
        pass


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
