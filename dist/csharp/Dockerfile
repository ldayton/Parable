FROM mcr.microsoft.com/dotnet/sdk:8.0
RUN dotnet --version | grep -q "^8\."
WORKDIR /workspace
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
