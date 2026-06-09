from flask import Flask, jsonify, request
import logging
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Get tracer
tracer = trace.get_tracer(__name__)

# Create Flask app
app = Flask(__name__)

# Instrument Flask and Requests
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
        span.set_attribute("operation", "list_trucks")
        span.set_attribute("truck_count", len(trucks))
        logger.info(f"Fetching all trucks. Count: {len(trucks)}")
        return jsonify(list(trucks.values())), 200

@app.route('/trucks/<truck_id>', methods=['GET'])
def get_truck(truck_id):
    with tracer.start_as_current_span("get_truck") as span:
        span.set_attribute("truck_id", truck_id)
        
        if truck_id in trucks:
            logger.info(f"Truck found: {truck_id}")
            span.set_attribute("status", "found")
            return jsonify(trucks[truck_id]), 200
        else:
            logger.warning(f"Truck not found: {truck_id}")
            span.set_attribute("status", "not_found")
            return jsonify({"error": "Truck not found"}), 404

@app.route('/trucks/register', methods=['POST'])
def register_truck():
    with tracer.start_as_current_span("register_truck") as span:
        data = request.json
        truck_id = str(len(trucks) + 1)
        
        span.set_attribute("truck_id", truck_id)
        span.set_attribute("truck_name", data.get("name"))
        
        new_truck = {
            "id": truck_id,
            "name": data.get("name", f"Truck-{truck_id}"),
            "status": "available",
            "location": data.get("location", "Unknown")
        }
        
        trucks[truck_id] = new_truck
        logger.info(f"Truck registered: {truck_id}")
        span.set_attribute("status", "registered")
        
        return jsonify(new_truck), 201

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Truck Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
