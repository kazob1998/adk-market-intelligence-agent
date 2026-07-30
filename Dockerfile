# Multi-stage production Dockerfile for ADK Agent
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim as runner

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PORT=8080
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "src.web.app:app", "--host", "0.0.0.0", "--port", "8080"]
