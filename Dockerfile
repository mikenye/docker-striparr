FROM alpine:3

RUN set -x && \
    apk add --no-cache \
      bash \
      file \
      ffmpeg \
      gnupg \
      py3-gunicorn \
      py3-pip \
      python3 \
      redis \
      && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    pip install --upgrade \
      pip \
      && \
    pip install \
      celery \
      flask \
      redis \
      requests \
      && \
    wget -q -O - https://raw.githubusercontent.com/mikenye/deploy-s6-overlay/master/deploy-s6-overlay.sh | sh && \
    apk del --no-cache \
      file \
      gnupg \
      py3-pip \
      && \
    rm -rf /tmp/*

COPY striparr.py /striparr.py
COPY manually_process.py /manually_process.py
COPY etc/ /etc/

ENTRYPOINT [ "/init" ]
