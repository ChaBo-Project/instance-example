#!/bin/sh

set -eu

: "${MONITORING_READ_TOKEN:?MONITORING_READ_TOKEN is required}"
: "${INSTANCE_URL:?INSTANCE_URL is required}"
: "${QDRANT_URL:?QDRANT_URL is required}"
: "${CHATUI_URL:?CHATUI_URL is required}"
: "${MONITORING_SCRAPE_INTERVAL:?MONITORING_SCRAPE_INTERVAL is required}"
: "${PROMETHEUS_RETENTION_TIME:?PROMETHEUS_RETENTION_TIME is required}"

umask 077

printf '%s' "${MONITORING_READ_TOKEN}" \
  > /tmp/monitoring-read-token

sed \
  -e "s|__MONITORING_SCRAPE_INTERVAL__|${MONITORING_SCRAPE_INTERVAL}|g" \
  -e "s|__INSTANCE_URL__|${INSTANCE_URL}|g" \
  -e "s|__QDRANT_URL__|${QDRANT_URL}|g" \
  -e "s|__CHATUI_URL__|${CHATUI_URL}|g" \
  /etc/prometheus/prometheus.yml.template \
  > /tmp/prometheus.yml

/bin/promtool check config /tmp/prometheus.yml

/bin/blackbox_exporter \
  --config.file=/etc/blackbox/blackbox.yml \
  --web.listen-address=127.0.0.1:9115 &

blackbox_pid=$!

/bin/prometheus \
  --config.file=/tmp/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time="${PROMETHEUS_RETENTION_TIME}" \
  --web.listen-address=0.0.0.0:7860 &

prometheus_pid=$!

stop_services() {
  trap - INT TERM

  kill -TERM "${prometheus_pid}" "${blackbox_pid}" 2>/dev/null || true
  wait "${prometheus_pid}" 2>/dev/null || true
  wait "${blackbox_pid}" 2>/dev/null || true
}

trap 'stop_services; exit 0' INT TERM

while kill -0 "${prometheus_pid}" 2>/dev/null &&
      kill -0 "${blackbox_pid}" 2>/dev/null; do
  sleep 5
done

echo "ERROR: Prometheus or Blackbox Exporter stopped unexpectedly."
stop_services
exit 1