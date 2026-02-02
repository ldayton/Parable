FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl libcurl4-openssl-dev libxml2-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz | tar -C /opt -xzf - \
    && /opt/swift-5.9.2-RELEASE-ubuntu22.04/usr/bin/swift --version | grep -q "5\.9\.2"
ENV PATH="/opt/swift-5.9.2-RELEASE-ubuntu22.04/usr/bin:${PATH}"
WORKDIR /workspace
