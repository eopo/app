# Prometheus Metrics Integration

Diese Anwendung exportiert Metriken im Prometheus-Format über den `/metrics` Endpoint.

## Endpoint

- **URL**: `/metrics`
- **Methode**: `GET`
- **Format**: Prometheus Text-Format

## Installation

Die erforderliche Abhängigkeit `prometheus-client` wurde bereits zu `pyproject.toml` hinzugefügt.

```bash
# Dependencies installieren
pip install -e .
# oder mit uv:
uv pip install -e .
```

## Verfügbare Metriken

### HTTP-Metriken (automatisch erfasst)

- **`simplelogin_http_requests_total`** (Counter)
  - Beschreibung: Gesamtzahl der HTTP-Requests
  - Labels: `method`, `endpoint`, `status`

- **`simplelogin_http_request_duration_seconds`** (Histogram)
  - Beschreibung: HTTP-Request-Dauer in Sekunden
  - Labels: `method`, `endpoint`

### Postfix-Queue-Metriken

- **`simplelogin_postfix_queue_size`** (Gauge)
  - Beschreibung: Größe der Postfix-Queues
  - Labels: `queue_type` (incoming, active, deferred)

### Anwendungsspezifische Metriken

Die folgenden Metriken sind vorbereitet und können in der Anwendung verwendet werden:

- **`simplelogin_active_users_total`** (Gauge)
  - Beschreibung: Anzahl aktiver Benutzer

- **`simplelogin_aliases_total`** (Gauge)
  - Beschreibung: Gesamtzahl der Aliase

- **`simplelogin_email_forwards_total`** (Counter)
  - Beschreibung: Anzahl weitergeleiteter E-Mails

- **`simplelogin_email_replies_total`** (Counter)
  - Beschreibung: Anzahl versendeter Antworten

- **`simplelogin_job_execution_seconds`** (Histogram)
  - Beschreibung: Job-Ausführungszeit in Sekunden
  - Labels: `job_name`

- **`simplelogin_job_failures_total`** (Counter)
  - Beschreibung: Anzahl fehlgeschlagener Jobs
  - Labels: `job_name`

### SpamAssassin (aktiv, wenn `ENABLE_SPAM_ASSASSIN` und `SPAMASSASSIN_HOST` gesetzt)

- **`simplelogin_spamassassin_score`** (Histogram)
  - Beschreibung: SpamAssassin Score pro Nachricht
  - Buckets: -5, 0, 2, 5, 10, 20, 50

- **`simplelogin_spamassassin_duration_seconds`** (Histogram)
  - Beschreibung: Dauer des Spam-Assassin Checks
  - Buckets: 0.05s … 300s

- **`simplelogin_spamassassin_results_total`** (Counter)
  - Beschreibung: Klassifikationsergebnisse
  - Labels: `result` (ham, spam, timeout, error)

## Verwendung in der Anwendung

Um eigene Metriken zu erfassen, importiere sie aus `app.prometheus_metrics`:

```python
from app.prometheus_metrics import (
    email_forwards_total,
    email_replies_total,
    active_users_total,
    job_execution_time,
  job_failures_total,
  spamassassin_score,
)

# Counter inkrementieren
email_forwards_total.inc()

# Gauge setzen
active_users_total.set(1234)

# Histogram für Zeitmessung
with job_execution_time.labels(job_name='sync_contacts').time():
    # Code hier ausführen
    pass

# SpamAssassin Score (nur wenn aktiviert)
spamassassin_score.observe(4.2)
```

## Prometheus-Konfiguration

Füge den folgenden Scrape-Job zu deiner `prometheus.yml` hinzu:

```yaml
scrape_configs:
  - job_name: 'simplelogin'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:7777']  # Passe den Port an
    metrics_path: '/metrics'
```

## Test

Du kannst die Metriken lokal testen:

```bash
# Server starten
python server.py

# Metriken abrufen
curl http://localhost:7777/metrics
```

## Sicherheit

Der `/metrics` Endpoint ist aktuell öffentlich zugänglich. Für Produktionsumgebungen solltest du:

1. Den Endpoint durch Firewall-Regeln schützen (nur vom Prometheus-Server erreichbar)
2. Oder Authentifizierung hinzufügen (Basic Auth, Bearer Token, etc.)
3. Oder einen separaten internen Port für Metriken verwenden

Beispiel für Basic Auth in NGINX:

```nginx
location /metrics {
    auth_basic "Prometheus Metrics";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:7777/metrics;
}
```

## Monitoring Dashboard

Du kannst Grafana verwenden, um die Metriken zu visualisieren. Beispiel-Queries:

```promql
# Request Rate
rate(simplelogin_http_requests_total[5m])

# P95 Response Time
histogram_quantile(0.95, rate(simplelogin_http_request_duration_seconds_bucket[5m]))

# Postfix Queue Size
simplelogin_postfix_queue_size{queue_type="incoming"}

# Error Rate
rate(simplelogin_http_requests_total{status=~"5.."}[5m])
```
