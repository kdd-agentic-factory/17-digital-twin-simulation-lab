FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.110" "uvicorn[standard]>=0.27" "pydantic>=2.6" "pydantic-settings>=2.2" \
    "pyyaml>=6.0" "numpy>=1.26" "pandas>=2.2" "scipy>=1.12" "scikit-learn>=1.4" \
    "httpx>=0.26" "kafka-python>=2.0" \
    "structlog>=24" "prometheus-client>=0.21" \
    "opentelemetry-api>=1.28" "opentelemetry-sdk>=1.28"

COPY src ./src
COPY data-contracts ./data-contracts
COPY reports ./reports

EXPOSE 8170

CMD ["uvicorn", "digital_twin_lab.main:app", "--host", "0.0.0.0", "--port", "8170"]
