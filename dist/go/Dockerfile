FROM golang:1.21
RUN go version | grep -q "go1\.21"
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
