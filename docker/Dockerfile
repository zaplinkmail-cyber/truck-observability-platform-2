FROM python:3.9-slim

ARG SERVICE_DIR
ARG SERVICE_PORT

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ${SERVICE_DIR} .

EXPOSE ${SERVICE_PORT}

CMD ["python", "app.py"]
