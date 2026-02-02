FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
        binutils \
        curl \
        git \
        gnupg2 \
        libc6-dev \
        libcurl4-openssl-dev \
        libedit2 \
        libgcc-13-dev \
        libncurses-dev \
        libpython3-dev \
        libsqlite3-0 \
        libstdc++-13-dev \
        libxml2-dev \
        libz3-dev \
        pkg-config \
        unzip \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz | tar -C /opt -xzf - \
    && /opt/swift-5.9.2-RELEASE-ubuntu22.04/usr/bin/swift --version | grep -q "5\.9\.2"
ENV PATH="/opt/swift-5.9.2-RELEASE-ubuntu22.04/usr/bin:${PATH}"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
