from app.build_info import SHA1, VERSION
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
    Prometheus metrics endpoint
    Returns metrics in Prometheus format
    """
    return generate_metrics_response()


@monitor_bp.route("/exception")
def test_exception():
    raise Exception("to make sure sentry works")
    return "never reach here"
