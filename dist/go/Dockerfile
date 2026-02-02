FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz | tar -C /usr/local -xzf - \
    && /usr/local/go/bin/go version | grep -q "go1\.21\.5"
ENV PATH="/usr/local/go/bin:${PATH}"
WORKDIR /workspace
