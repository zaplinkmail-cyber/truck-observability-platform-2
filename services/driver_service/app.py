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

resource = Resource.create({"service.name": "driver-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Sample data
drivers = {
    "1": {"id": "1", "name": "Driver-001", "status": "available", "rating": 4.5},
    "2": {"id": "2", "name": "Driver-002", "status": "available", "rating": 4.2},
    "3": {"id": "3", "name": "Driver-003", "status": "on_duty",   "rating": 4.8},
}

@app.route('/drivers', methods=['GET'])
def get_drivers():
    with tracer.start_as_current_span("get_drivers") as span:
        span.set_attribute("driver_count", len(drivers))
        logger.info(f"Fetching all drivers. Count: {len(drivers)}")
        return jsonify(list(drivers.values())), 200

# ✅ Static route BEFORE dynamic route
@app.route('/drivers/assign-truck', methods=['POST'])
def assign_truck():
    with tracer.start_as_current_span("assign_truck") as span:
        data = request.json or {}
        driver_id = data.get("driver_id", "1")
        truck_id = data.get("truck_id", "1")
        span.set_attribute("driver_id", driver_id)
        span.set_attribute("truck_id", truck_id)

        if driver_id not in drivers:
            span.set_attribute("status", "driver_not_found")
            logger.warning(f"Driver not found: {driver_id}")
            return jsonify({"error": "Driver not found"}), 404

        drivers[driver_id]["status"] = "assigned"
        span.set_attribute("status", "assigned")
        logger.info(f"Driver {driver_id} assigned to truck {truck_id}")
        return jsonify({
            "driver_id": driver_id,
            "truck_id": truck_id,
            "status": "assigned"
        }), 200

@app.route('/drivers/<driver_id>', methods=['GET'])
def get_driver(driver_id):
    with tracer.start_as_current_span("get_driver") as span:
        span.set_attribute("driver_id", driver_id)
        if driver_id in drivers:
            span.set_attribute("status", "found")
            logger.info(f"Driver found: {driver_id}")
            return jsonify(drivers[driver_id]), 200
        else:
            span.set_attribute("status", "not_found")
            logger.warning(f"Driver not found: {driver_id}")
            return jsonify({"error": "Driver not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Driver Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)