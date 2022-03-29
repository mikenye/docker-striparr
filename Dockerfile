FROM debian:bullseye-20220328-slim

ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    ALERT_EMAIL_SMTP_PORT=25 \
    ALERT_FREQUENCY=600

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY rootfs/ /

RUN set -x && \
    TEMP_PACKAGES=() && \
    KEPT_PACKAGES=() && \
    # Dependencies for s6-overlay
    TEMP_PACKAGES+=(ca-certificates) && \
    TEMP_PACKAGES+=(curl) && \
    TEMP_PACKAGES+=(file) && \
    TEMP_PACKAGES+=(gnupg) && \
    # Dependencies for striparr
    KEPT_PACKAGES+=(ffmpeg) && \
    KEPT_PACKAGES+=(gunicorn3) && \
    KEPT_PACKATES+=(python3) && \
    KEPT_PACKAGES+=(python3-gunicorn) && \
    TEMP_PACKAGES+=(python3-pip) && \
    KEPT_PACKAGES+=(python3-setuptools) && \
    KEPT_PACKAGES+=(python3-six) && \
    KEPT_PACKAGES+=(redis) && \
    # Install swaks for email alerting
    KEPT_PACKAGES+=(swaks) && \
    KEPT_PACKAGES+=(libnet-ssleay-perl) && \
    # Install packages.
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ${KEPT_PACKAGES[@]} \
        ${TEMP_PACKAGES[@]} \
        && \
    # Provide symlinks for python
    ln -s /usr/bin/python3 /usr/bin/python && \
    # Install python packages
    python3 -m pip install --no-cache-dir --upgrade \
      pip \
      && \
    python3 -m pip install --no-cache-dir \
      celery \
      flask \
      redis \
      requests \
      && \
    # Create log dirs
    mkdir -p /var/log/listener && \
    mkdir -p /var/log/worker && \
    chown nobody /var/log/listener && \
    chown nobody /var/log/worker && \
    # Deploy s6-overlay
    curl -s https://raw.githubusercontent.com/mikenye/deploy-s6-overlay/master/deploy-s6-overlay.sh | sh && \
    # Clean-up
    apt-get remove -y ${TEMP_PACKAGES[@]} && \
    apt-get autoremove -y && \
    rm -rf /src/* /tmp/* /var/lib/apt/lists/* && \
    # Versions
    echo "Celery $(python3 -m celery --version)" && \
    python3 -m flask --version && \
    redis-server --version

ENTRYPOINT [ "/init" ]
