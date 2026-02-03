FROM node:21
RUN node --version | grep -q "v21\."
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
