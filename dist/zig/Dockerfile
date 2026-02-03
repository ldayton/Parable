FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ]; then ZIG_ARCH="aarch64"; else ZIG_ARCH="x86_64"; fi \
    && curl -sSL "https://ziglang.org/download/0.11.0/zig-linux-${ZIG_ARCH}-0.11.0.tar.xz" | tar -C /usr/local -xJf - \
    && ln -s /usr/local/zig-linux-${ZIG_ARCH}-0.11.0/zig /usr/local/bin/zig \
    && zig version | grep -q "0\.11\.0"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
