FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y lua5.4 \
    && rm -rf /var/lib/apt/lists/* \
    && lua5.4 -v 2>&1 | grep -q "5\.4" \
    && ln -s /usr/bin/lua5.4 /usr/bin/lua \
    && ln -s /usr/bin/luac5.4 /usr/bin/luac
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
