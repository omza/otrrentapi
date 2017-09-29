FROM omza/alpine-nginx-py3-supervisor
MAINTAINER oliver@app-workshop.de

# ARGs & ENVs
# -------------------------------------------------------
ENV NGINX_CONFIG /usr/src/api/config/nginx.api.conf
ENV APPLICATION_ENVIRONMENT Production

# dirs & volumes
# --------------------------------------------------------
RUN mkdir -p /usr/src/api \
	&& mkdir -p /usr/log \
	&& mkdir -p /usr/src/etl/config/secrets/

WORKDIR /usr/src/api
COPY . /usr/src/api

VOLUME /usr/src/api/
VOLUME /usr/log/
VOLUME /usr/src/api/config/secrets/

# Install requirements
# ----------------------------------------------------------
COPY requirements.txt /usr/src/api/
RUN apk update && \
    apk upgrade && \
    apk add -u build-base openssl-dev libffi-dev && \
	pip install --no-cache-dir -r requirements.txt && \
	apk del build-base

# Start & Stop
# -----------------------------------------------------------
EXPOSE 80
STOPSIGNAL SIGTERM
ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/usr/src/api/config/supervisord.conf"]