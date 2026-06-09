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

resource = Resource.create({"service.name": "shipment-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

shipments = {}
shipment_counter = 0

@app.route('/shipments', methods=['GET'])
def get_shipments():
    with tracer.start_as_current_span("get_shipments") as span:
        span.set_attribute("shipment_count", len(shipments))
        logger.info(f"Fetching all shipments. Count: {len(shipments)}")
        return jsonify(list(shipments.values())), 200

@app.route('/shipments/create', methods=['POST'])
def create_shipment():
    global shipment_counter
    with tracer.start_as_current_span("create_shipment") as span:
        shipment_counter += 1
        shipment_id = f"SHP-{shipment_counter:05d}"
        data = request.json or {}
        truck_id = data.get("truck_id", "1")
        driver_id = data.get("driver_id", "1")

        span.set_attribute("shipment_id", shipment_id)
        span.set_attribute("truck_id", truck_id)
        span.set_attribute("driver_id", driver_id)
        logger.info(f"Creating shipment: {shipment_id}")

        # Call Truck Service
        with tracer.start_as_current_span("call_truck_service") as truck_span:
            try:
                truck_response = requests.get(
                    f"http://truck-service:5001/trucks/{truck_id}", timeout=5
                )
                truck_span.set_attribute("http.status_code", truck_response.status_code)
                logger.info(f"Truck service responded: {truck_response.status_code}")
            except Exception as e:
                truck_span.set_attribute("error", True)
                logger.error(f"Truck service error: {e}")

        # Call Driver Service
        with tracer.start_as_current_span("call_driver_service") as driver_span:
            try:
                driver_response = requests.get(
                    f"http://driver-service:5003/drivers/{driver_id}", timeout=5
                )
                driver_span.set_attribute("http.status_code", driver_response.status_code)
                logger.info(f"Driver service responded: {driver_response.status_code}")
            except Exception as e:
                driver_span.set_attribute("error", True)
                logger.error(f"Driver service error: {e}")

        new_shipment = {
            "id": shipment_id,
            "truck_id": truck_id,
            "driver_id": driver_id,
            "status": "created",
            "order_id": data.get("order_id", f"ORD-{shipment_counter}")
        }
        shipments[shipment_id] = new_shipment
        span.set_attribute("status", "created")
        logger.info(f"Shipment created: {shipment_id}")
        return jsonify(new_shipment), 201

@app.route('/shipments/<shipment_id>/status', methods=['PATCH'])
def update_shipment_status(shipment_id):
    with tracer.start_as_current_span("update_shipment_status") as span:
        if shipment_id not in shipments:
            return jsonify({"error": "Shipment not found"}), 404
        data = request.json or {}
        new_status = data.get("status", "pending")
        shipments[shipment_id]["status"] = new_status
        span.set_attribute("shipment_id", shipment_id)
        span.set_attribute("new_status", new_status)
        logger.info(f"Shipment status updated: {shipment_id} -> {new_status}")
        return jsonify(shipments[shipment_id]), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Shipment Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)