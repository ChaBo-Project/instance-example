---
title: ChaBo Grafana
emoji: 📈
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# ChaBo Grafana

This private Docker Space displays monitoring information collected by the
ChaBo Prometheus Space.

The Space requires these runtime variables:

- `PROMETHEUS_URL`
- `GF_SERVER_ROOT_URL`

It requires these runtime secrets:

- `MONITORING_READ_TOKEN`
- `GF_SECURITY_ADMIN_PASSWORD`

Anonymous access and user registration are disabled. The Prometheus datasource
and ChaBo dashboard are provisioned automatically.