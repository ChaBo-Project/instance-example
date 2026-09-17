---
title: ChaBo Prometheus
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ChaBo Prometheus

This private Docker Space provides optional monitoring for a ChaBo instance.

It runs:

- Prometheus for collecting and storing monitoring data
- Blackbox Exporter for checking the Orchestrator, Qdrant and ChatUI endpoints

The Space requires these runtime variables:

- `INSTANCE_URL`
- `QDRANT_URL`
- `CHATUI_URL`
- `MONITORING_SCRAPE_INTERVAL`
- `PROMETHEUS_RETENTION_TIME`

It also requires the `MONITORING_READ_TOKEN` runtime secret.

Monitoring data stored on the default Space filesystem is temporary and is
lost when the Space restarts. Attach persistent storage when historical data
must be retained.
