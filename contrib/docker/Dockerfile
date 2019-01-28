FROM alpine:3.8
MAINTAINER "nzlosh@yahoo.com"

RUN apk add --no-cache python3 gcc python3-dev openssl-dev libffi-dev musl-dev git&& \
	python3 -m ensurepip && \
	rm -r /usr/lib/python*/ensurepip && \
	pip3 install --upgrade pip setuptools && \
	if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
	if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
	rm -r /root/.cache && \
	pip3 install errbot && \
	mkdir -p /opt/errbot && \
	cd /opt/errbot && errbot --init
ENTRYPOINT errbot -c /opt/errbot/config.py
