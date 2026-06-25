from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

WS_CONNECTIONS_TOTAL = Counter("chat_ws_connections_total", "Total WebSocket connections", ["result"])
WS_ACTIVE_CONNECTIONS = Gauge("chat_ws_active_connections", "Active WebSocket connections")
ACTIVE_USERS = Gauge("chat_active_users", "Active users seen by this backend instance")
ACTIVE_ROOMS = Gauge("chat_active_rooms", "Rooms with active local subscribers")
MESSAGES_SENT = Counter("chat_messages_sent_total", "Messages accepted by the server")
MESSAGES_RECEIVED = Counter("chat_messages_received_total", "Events received from WebSocket clients")
MESSAGE_LATENCY = Histogram("chat_message_processing_seconds", "Message processing latency seconds", buckets=(0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2,5))
DB_WRITE_LATENCY = Histogram("chat_db_write_seconds", "DB write latency seconds")
REDIS_PUBLISH_LATENCY = Histogram("chat_redis_publish_seconds", "Redis publish latency seconds")
ML_LATENCY = Histogram("chat_ml_inference_seconds", "ML inference latency seconds", buckets=(0.001,0.005,0.01,0.025,0.05,0.1,0.25,0.5,1))
ML_PREDICTIONS = Counter("chat_ml_predictions_total", "ML predictions by label", ["label", "model_version"])
RATE_LIMIT_EVENTS = Counter("chat_rate_limit_events_total", "Rate-limit events")
WS_ERRORS = Counter("chat_ws_errors_total", "WebSocket error events", ["type"])

def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
