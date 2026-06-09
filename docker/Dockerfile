FROM python:3.9-slim

ARG SERVICE_DIR
ARG SERVICE_PORT

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ${SERVICE_DIR} .

EXPOSE ${SERVICE_PORT}

CMD ["python", "app.py"]