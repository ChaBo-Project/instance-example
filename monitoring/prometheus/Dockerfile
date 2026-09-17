FROM quay.io/prometheus/prometheus:v3.14.0 AS prometheus
FROM quay.io/prometheus/blackbox-exporter:v0.28.0 AS blackbox

FROM alpine:3.22.1

RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates \
    && addgroup --system --gid 1000 user \
    && adduser --system --disabled-password --uid 1000 \
        --ingroup user user \
    && mkdir -p /app /prometheus /etc/prometheus /etc/blackbox \
    && chown -R user:user \
        /app /prometheus /etc/prometheus /etc/blackbox

COPY --from=prometheus /bin/prometheus /bin/prometheus
COPY --from=prometheus /bin/promtool /bin/promtool
COPY --from=blackbox /bin/blackbox_exporter /bin/blackbox_exporter

COPY --chown=user:user prometheus.yml.template \
    /etc/prometheus/prometheus.yml.template
COPY --chown=user:user blackbox.yml /etc/blackbox/blackbox.yml
COPY --chown=user:user start.sh /app/start.sh

RUN chmod 0555 \
    /app/start.sh \
    /bin/prometheus \
    /bin/promtool \
    /bin/blackbox_exporter

USER user
WORKDIR /app

EXPOSE 7860

ENTRYPOINT ["/app/start.sh"]