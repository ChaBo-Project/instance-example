FROM grafana/grafana:13.2.2

USER root

RUN addgroup --system --gid 1000 hfuser \
    && adduser --system --disabled-password --uid 1000 \
        --ingroup hfuser hfuser \
    && mkdir -p /var/lib/grafana/dashboards \
    && chown -R 1000:1000 \
        /var/lib/grafana \
        /var/log/grafana \
        /etc/grafana

COPY --chown=1000:1000 provisioning/ \
    /etc/grafana/provisioning/
COPY --chown=1000:1000 dashboards/ \
    /var/lib/grafana/dashboards/

USER 1000

ENV GF_SERVER_HTTP_ADDR=0.0.0.0 \
    GF_SERVER_HTTP_PORT=7860 \
    GF_USERS_ALLOW_SIGN_UP=false \
    GF_AUTH_ANONYMOUS_ENABLED=false \
    GF_SECURITY_COOKIE_SECURE=true \
    GF_SECURITY_COOKIE_SAMESITE=none \
    GF_SECURITY_ALLOW_EMBEDDING=true \
    GF_SECURITY_DISABLE_GRAVATAR=true \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    GF_ANALYTICS_CHECK_FOR_UPDATES=false

EXPOSE 7860