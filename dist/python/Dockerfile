FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3.12 python3.12-venv curl \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 --version | grep -q "3\.12" \
    && curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
