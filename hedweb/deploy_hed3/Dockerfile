FROM python:3.7-alpine
COPY ./requirements.txt /root/
WORKDIR /root
RUN apk add --no-cache gcc \
build-base \
linux-headers \
musl-dev \
openrc \
libxslt-dev \
libxml2-dev \
apache2 \
apache2-dev && \
pip3 install --upgrade pip && \
pip3 install -r requirements.txt
COPY ./httpd.conf /etc/apache2/httpd.conf
COPY ./hedtools3 /var/www/hedtools3/
RUN mkdir -p /run/apache2 && \
mkdir -p /var/log/hedtools3 && \
chown -R apache:apache /var/log/hedtools3 && \
mkdir -p /var/cache/hed_cache3 && \
chown -R apache:apache /var/cache/hed_cache3
ENTRYPOINT /usr/sbin/httpd -D FOREGROUND -f /etc/apache2/httpd.conf
ENV HEDTOOLS_CONFIG_CLASS=config.ProductionConfig
