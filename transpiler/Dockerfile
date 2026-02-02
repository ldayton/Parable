FROM python:3.12-slim
RUN pip install uv
WORKDIR /transpiler
COPY . .
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
