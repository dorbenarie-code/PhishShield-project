FROM python:3.12-slim

WORKDIR /app

# Copy source and config
COPY pyproject.toml ./
COPY app ./app

# Install dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
