FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mock/ mock/
# Production: listen on all interfaces, keep guides on the mounted volume, no local Claude Code agent.
ENV HOST=0.0.0.0 PORT=8080 DATA_DIR=/data LOCAL_AGENT=0 PYTHONUNBUFFERED=1
RUN useradd --create-home app && mkdir -p /data && chown app /data
USER app
EXPOSE 8080
CMD ["python", "mock/server.py"]
