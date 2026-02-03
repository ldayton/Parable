FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:ondrej/php \
    && apt-get update && apt-get install -y php8.3-cli php8.3-mbstring php8.3-intl \
    && rm -rf /var/lib/apt/lists/* \
    && php --version | head -1 | grep -q "8\.3"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
