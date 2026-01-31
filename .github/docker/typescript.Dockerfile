FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://nodejs.org/dist/v21.7.3/node-v21.7.3-linux-x64.tar.xz | tar -C /usr/local -xJf - --strip-components=1 \
    && npm install -g typescript@5.3 \
    && tsc --version | grep -q "5\.3"
WORKDIR /workspace
