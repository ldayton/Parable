FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl unzip git \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://storage.googleapis.com/dart-archive/channels/stable/release/3.2.6/sdk/dartsdk-linux-x64-release.zip -o /tmp/dart.zip \
    && unzip -q /tmp/dart.zip -d /opt \
    && rm /tmp/dart.zip \
    && /opt/dart-sdk/bin/dart --version 2>&1 | grep -q "3\.2\.6"
ENV PATH="/opt/dart-sdk/bin:${PATH}"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
