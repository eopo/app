"""
Prometheus metrics for SimpleLogin
"""

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Dummy classes if prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def set(self, *args, **kwargs):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def observe(self, *args, **kwargs):
            pass


if PROMETHEUS_AVAILABLE:
    # Create a custom registry to avoid conflicts with other prometheus integrations
    registry = CollectorRegistry()

    # HTTP Request metrics
    http_requests_total = Counter(
        "simplelogin_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
        registry=registry,
    )

    http_request_duration_seconds = Histogram(
        "simplelogin_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf")),
        registry=registry,
    )

    # Application-specific metrics
    active_users_total = Gauge(
        "simplelogin_active_users_total",
        "Total number of active users",
        registry=registry,
    )

    aliases_total = Gauge(
        "simplelogin_aliases_total", "Total number of aliases", registry=registry
    )

    email_forwards_total = Counter(
        "simplelogin_email_forwards_total",
        "Total number of forwarded emails",
        registry=registry,
    )

    email_replies_total = Counter(
        "simplelogin_email_replies_total",
        "Total number of email replies",
        registry=registry,
    )

    # Postfix queue metrics
    postfix_queue_size = Gauge(
        "simplelogin_postfix_queue_size",
        "Size of postfix queues",
        ["queue_type"],
        registry=registry,
    )

    # Job metrics
    job_execution_time = Histogram(
        "simplelogin_job_execution_seconds",
        "Job execution time in seconds",
        ["job_name"],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
        registry=registry,
    )

    job_failures_total = Counter(
        "simplelogin_job_failures_total",
        "Total number of job failures",
        ["job_name"],
        registry=registry,
    )

    # SpamAssassin metrics (emitted only when SpamAssassin is enabled)
    spamassassin_score = Histogram(
        "simplelogin_spamassassin_score",
        "SpamAssassin score per message",
        buckets=(-5, 0, 2, 5, 10, 20, 50, float("inf")),
        registry=registry,
    )

    spamassassin_duration_seconds = Histogram(
        "simplelogin_spamassassin_duration_seconds",
        "SpamAssassin check duration in seconds",
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
        registry=registry,
    )

    spamassassin_results_total = Counter(
        "simplelogin_spamassassin_results_total",
        "SpamAssassin classification results",
        ["result"],
        registry=registry,
    )
else:
    # Create dummy metrics if prometheus_client is not available
    registry = None
    http_requests_total = Counter()
    http_request_duration_seconds = Histogram()
    active_users_total = Gauge()
    aliases_total = Gauge()
    email_forwards_total = Counter()
    email_replies_total = Counter()
    postfix_queue_size = Gauge()
    job_execution_time = Histogram()
    job_failures_total = Counter()
    spamassassin_score = Histogram()
    spamassassin_duration_seconds = Histogram()
    spamassassin_results_total = Counter()


def generate_metrics_response():
    """
    Generate Prometheus metrics response
    """
    from flask import Response

    if not PROMETHEUS_AVAILABLE:
        return Response(
            "Prometheus client not installed. Run: pip install prometheus-client",
            mimetype="text/plain",
            status=503,
        )

    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


class PrometheusMiddleware:
    """
    Flask middleware to track HTTP request metrics
    """

    def __init__(self, app):
        if not PROMETHEUS_AVAILABLE:
            return  # Skip initialization if prometheus_client not available

        self.app = app
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        import time

        if not PROMETHEUS_AVAILABLE:
            return
        from flask import g

        g.prom_start_time = time.time()

    def _after_request(self, response):
        import time

        if not PROMETHEUS_AVAILABLE:
            return response

        from flask import g, request

        # Skip metrics endpoint itself to avoid recursion
        if request.path == "/metrics":
            return response

        # Skip static files
        if request.path.startswith("/static"):
            return response

        # Calculate request duration
        if hasattr(g, "prom_start_time"):
            duration = time.time() - g.prom_start_time

            # Get endpoint name
            endpoint = request.endpoint or "unknown"

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

        return response
