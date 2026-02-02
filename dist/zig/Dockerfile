FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl xz-utils git \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://ziglang.org/download/0.11.0/zig-linux-x86_64-0.11.0.tar.xz | tar -C /usr/local -xJf - \
    && ln -s /usr/local/zig-linux-x86_64-0.11.0/zig /usr/local/bin/zig \
    && zig version | grep -q "0\.11\.0"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
