FROM python:3.13-alpine

RUN adduser -D -u 1001 appuser

WORKDIR /app

ARG VERSION=1.0.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    DEBUG=False \
    VERSION=${VERSION}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /data && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
