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
drivers = {
    "1": {"id": "1", "name": "Driver-001", "status": "available", "rating": 4.5},
    "2": {"id": "2", "name": "Driver-002", "status": "available", "rating": 4.2},
    "3": {"id": "3", "name": "Driver-003", "status": "on_duty", "rating": 4.8},
}

@app.route('/drivers', methods=['GET'])
def get_drivers():
    with tracer.start_as_current_span("get_drivers") as span:
        span.set_attribute("operation", "list_drivers")
        span.set_attribute("driver_count", len(drivers))
        logger.info(f"Fetching all drivers. Count: {len(drivers)}")
        return jsonify(list(drivers.values())), 200

@app.route('/drivers/<driver_id>', methods=['GET'])
def get_driver(driver_id):
    with tracer.start_as_current_span("get_driver") as span:
        span.set_attribute("driver_id", driver_id)
        
        if driver_id in drivers:
            logger.info(f"Driver found: {driver_id}")
            span.set_attribute("status", "found")
            return jsonify(drivers[driver_id]), 200
        else:
            logger.warning(f"Driver not found: {driver_id}")
            span.set_attribute("status", "not_found")
            return jsonify({"error": "Driver not found"}), 404

@app.route('/drivers/assign-truck', methods=['POST'])
def assign_truck():
    with tracer.start_as_current_span("assign_truck") as span:
        data = request.json
        driver_id = data.get("driver_id", "1")
        truck_id = data.get("truck_id", "1")
        
        span.set_attribute("driver_id", driver_id)
        span.set_attribute("truck_id", truck_id)
        
        if driver_id not in drivers:
            logger.warning(f"Driver not found: {driver_id}")
            span.set_attribute("status", "driver_not_found")
            return jsonify({"error": "Driver not found"}), 404
        
        # Update driver status
        drivers[driver_id]["status"] = "assigned"
        logger.info(f"Driver assigned to truck: {driver_id} -> {truck_id}")
        span.set_attribute("status", "assigned")
        
        return jsonify({
            "driver_id": driver_id,
            "truck_id": truck_id,
            "status": "assigned"
        }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Driver Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)
