FROM omza/flask-deploy-stack:onbuild
MAINTAINER oliver@app-workshop.de

# ARGs & ENVs
# -------------------------------------------------------
ENV APPLICATION_ENVIRONMENT Production

# dirs & volumes
# --------------------------------------------------------
RUN mkdir -p /usr/src/api \
	&& mkdir -p /usr/src/api/config/secrets/

VOLUME /usr/src/api/
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
#STOPSIGNAL SIGTERM

#ENTRYPOINT ["gunicorn", "--config", "./config/gunicorn.conf.py", "otrrentapi:app"]