FROM python:3.6-alpine
MAINTAINER oliver@app-workshop.de

# ARGs & ENVs
# -------------------------------------------------------
ENV APPLICATION_ENVIRONMENT Test

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
RUN pip install --no-cache-dir -r requirements.txt

# Start & Stop
# -----------------------------------------------------------
STOPSIGNAL SIGTERM
ENTRYPOINT ["gunicorn", "--config", "./config/gunicorn.conf.py", "otrrentapi:app"] 