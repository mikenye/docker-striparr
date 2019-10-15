FROM alpine:3

ENV \
  S6_URL=https://github.com/just-containers/s6-overlay/releases/download/v1.22.1.0/s6-overlay-amd64.tar.gz

ADD ${S6_URL} /tmp/s6-overlay.tar.gz 

RUN \
  apk add --no-cache python3 py3-pip py3-gunicorn redis ffmpeg && \
  ln -s /usr/bin/python3 /usr/bin/python && \
  ln -s /usr/bin/pip3 /usr/bin/pip && \
  pip install --upgrade pip && \
  pip install flask celery redis requests && \
  tar -xzf /tmp/s6-overlay.tar.gz -C / && \
  rm -rf /tmp/*

COPY striparr.py /striparr.py
COPY manually_process.py /manually_process.py
COPY etc/ /etc/

ENTRYPOINT [ "/init" ]

