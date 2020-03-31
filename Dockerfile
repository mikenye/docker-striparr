FROM alpine:3

RUN set -x && \
    apk add --no-cache \
      python3 \
      py3-pip \
      py3-gunicorn \
      redis \
      ffmpeg \
      gnupg \
      && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    pip install --upgrade \
      pip \
      && \
    pip install \
      flask \
      celery \
      redis \
      requests \
      && \
    wget -q -O - https://raw.githubusercontent.com/mikenye/deploy-s6-overlay/master/deploy-s6-overlay.sh | sh && \
    apk del --no-cache \
      gnupg \
      py3-pip \
      && \
    rm -rf /tmp/*

COPY striparr.py /striparr.py
COPY manually_process.py /manually_process.py
COPY etc/ /etc/

ENTRYPOINT [ "/init" ]
