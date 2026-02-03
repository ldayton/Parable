FROM node:21
RUN npm install -g typescript@5.3 \
    && tsc --version | grep -q "5\.3"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
