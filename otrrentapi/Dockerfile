FROM python:alpine3.6
MAINTAINER oliver@app-workshop.de

# ARGs & ENVs
# -------------------------------------------------------
ENV APPLICATION_ENVIRONMENT Production

# dirs & volumes
# --------------------------------------------------------
RUN mkdir -p /usr/src/api \
	&& mkdir -p /usr/log \
	&& mkdir -p /usr/src/etl/config/secrets/


VOLUME /usr/src/api/
VOLUME /usr/log/
VOLUME /usr/src/api/config/secrets/

# Install docker context
# ----------------------------------------------------------
COPY . /usr/src/api
WORKDIR /usr/src/api


# Install requirements
# ----------------------------------------------------------
RUN apk update && \
    apk upgrade && \
    apk add -u build-base openssl-dev libffi-dev && \
	pip install --no-cache-dir gunicorn && \
	pip install --no-cache-dir -r requirements.txt && \
	apk del build-base

# Start & Stop
# -----------------------------------------------------------
EXPOSE 8000
STOPSIGNAL SIGTERM

ENTRYPOINT ["gunicorn", "--config", "./config/gunicorn.conf.py", "otrrentapi:app"]