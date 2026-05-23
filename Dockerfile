FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scenarios ./scenarios
COPY data-contracts ./data-contracts
COPY reports/templates ./reports/templates

RUN pip install --no-cache-dir .

EXPOSE 8170

CMD ["uvicorn", "digital_twin_lab.api.app:app", "--host", "0.0.0.0", "--port", "8170"]
