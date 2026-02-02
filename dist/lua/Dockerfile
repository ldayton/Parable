FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y lua5.4 \
    && rm -rf /var/lib/apt/lists/* \
    && lua5.4 -v 2>&1 | grep -q "5\.4"
WORKDIR /workspace
