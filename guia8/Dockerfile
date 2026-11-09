FROM python:3.12-slim
WORKDIR /service
COPY app/ /service/app/
RUN mkdir -p /service/data && useradd -r -u 10001 demo && chown -R demo /service/data
ENV DATABASE_PATH=/service/data/comercio.db PORT=8080 PYTHONDONTWRITEBYTECODE=1
USER demo
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=2)" || exit 1
CMD ["python", "app/server.py"]
