from flask import Flask, jsonify, request
import logging
import os
import requests

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OTLP Exporter → Jaeger via HTTP
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318")
exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")

resource = Resource.create({"service.name": "truck-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Sample data
trucks = {
    "1": {"id": "1", "name": "Truck-001", "status": "available", "location": "Delhi"},
    "2": {"id": "2", "name": "Truck-002", "status": "available", "location": "Mumbai"},
    "3": {"id": "3", "name": "Truck-003", "status": "in_transit", "location": "Bangalore"},
}

@app.route('/trucks', methods=['GET'])
def get_trucks():
    with tracer.start_as_current_span("get_trucks") as span:
        span.set_attribute("truck_count", len(trucks))
        logger.info(f"Fetching all trucks. Count: {len(trucks)}")
        return jsonify(list(trucks.values())), 200

@app.route('/trucks/register', methods=['POST'])
def register_truck():
    with tracer.start_as_current_span("register_truck") as span:
        data = request.json or {}
        truck_id = str(len(trucks) + 1)
        new_truck = {
            "id": truck_id,
            "name": data.get("name", f"Truck-{truck_id}"),
            "status": "available",
            "location": data.get("location", "Unknown")
        }
        trucks[truck_id] = new_truck
        span.set_attribute("truck_id", truck_id)
        span.set_attribute("status", "registered")
        logger.info(f"Truck registered: {truck_id}")
        return jsonify(new_truck), 201

@app.route('/trucks/<truck_id>', methods=['GET'])
def get_truck(truck_id):
    with tracer.start_as_current_span("get_truck") as span:
        span.set_attribute("truck_id", truck_id)
        if truck_id in trucks:
            span.set_attribute("status", "found")
            logger.info(f"Truck found: {truck_id}")
            return jsonify(trucks[truck_id]), 200
        else:
            span.set_attribute("status", "not_found")
            logger.warning(f"Truck not found: {truck_id}")
            return jsonify({"error": "Truck not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Truck Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)