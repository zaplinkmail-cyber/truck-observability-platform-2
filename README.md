# Truck Observability Platform

A comprehensive observability solution for a distributed truck fleet management system using OpenTelemetry, Jaeger, and Splunk.

## 📌 Quick Start

### Prerequisites
- Docker
- Docker Compose
- Git

### Run Services

```bash
docker-compose up -d
```

### Access Jaeger UI
Open browser: `http://localhost:16686`

### Test Services

```bash
# Get all trucks
curl http://localhost:5001/trucks

# Create shipment
curl -X POST http://localhost:5002/shipments/create \
  -H "Content-Type: application/json" \
  -d '{"truck_id":"1","driver_id":"1","order_id":"ORD-001"}'

# Get all drivers
curl http://localhost:5003/drivers
```

## 🏗️ Services

### Truck Service (Port 5001)
- `GET /trucks` - List all trucks
- `POST /trucks/register` - Register new truck
- `GET /trucks/{id}` - Get truck details

### Shipment Service (Port 5002)
- `GET /shipments` - List all shipments
- `POST /shipments/create` - Create shipment
- `PATCH /shipments/{id}/status` - Update status

### Driver Service (Port 5003)
- `GET /drivers` - List all drivers
- `GET /drivers/{id}` - Get driver details
- `POST /drivers/assign-truck` - Assign driver

## 🔍 Observability Features

### Traces
- Complete request flow visualization
- Service call timing
- Context propagation between services

### Metrics (Coming Day 2)
- Request latency
- Error rates
- Throughput

### Logs
- Structured logging from each service
- Integrated with traces

## 🚀 Day 1 Deliverables

✅ 3 instrumented microservices
✅ OpenTelemetry integration
✅ Jaeger backend
✅ Docker Compose setup
✅ Context propagation
✅ Traces visible in UI

## 📚 Technologies

- **OpenTelemetry**: Instrumentation
- **Jaeger**: Distributed tracing
- **Flask**: Web framework
- **Docker**: Containerization
- **Python**: Service implementation

## 📝 Next Steps

- Day 2: Add metrics and dashboards
- Day 3: Chaos injection scenarios
- Day 4: Incident investigation
- Day 5: AI-powered analysis
