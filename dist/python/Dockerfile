FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3.12 python3.12-venv \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 --version | grep -q "3\.12"
WORKDIR /workspace
