FROM python:3.12-slim
RUN pip install uv
ENV UV_PROJECT_ENVIRONMENT=/venv
WORKDIR /transpiler
# Code is mounted at runtime, not copied - ensures changes are always picked up
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
