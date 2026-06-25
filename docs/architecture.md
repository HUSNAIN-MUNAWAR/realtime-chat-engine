# Architecture

```mermaid
flowchart LR
  UI[Next.js dashboard] -->|REST + JWT| API[FastAPI API]
  UI -->|WebSocket JWT| WS[WebSocket Gateway]
  WS --> CM[Connection Manager]
  WS --> RL[Redis Rate Limiter]
  WS --> DB[(PostgreSQL)]
  WS --> ML[Risk Scoring Model]
  WS --> R[(Redis Pub/Sub)]
  R --> WS2[Other backend instances]
  API --> DB
  API --> MET[/Prometheus metrics/]
  PROM[Prometheus] --> MET
  GRAF[Grafana] --> PROM
```

The backend can run as multiple instances behind NGINX/LB because room fanout is not stored only in process memory. Each instance keeps its own local WebSocket connections, and Redis pub/sub carries events across instances.

## Message lifecycle

```mermaid
sequenceDiagram
  participant C as Client
  participant WS as FastAPI WebSocket
  participant PG as PostgreSQL
  participant ML as Risk Model
  participant R as Redis Pub/Sub
  participant O as Other Clients
  C->>WS: message.send(client_message_id)
  WS->>WS: validate JWT, membership, size, rate limit
  WS->>PG: check idempotency
  WS->>ML: score content
  WS->>PG: insert message + risk_score
  WS-->>C: message.ack(status=sent)
  WS->>R: publish message.created
  R->>O: fanout to local room subscribers
  O-->>WS: message.delivered / message.read
  WS->>PG: persist receipts
```

## Redis fanout

```mermaid
flowchart TB
  subgraph Instance A
    A1[WS clients room-1]
    A2[Connection manager]
  end
  subgraph Instance B
    B1[WS clients room-1]
    B2[Connection manager]
  end
  A2 -->|publish chat:events| REDIS[(Redis Pub/Sub)]
  REDIS --> A2
  REDIS --> B2
  A2 --> A1
  B2 --> B1
```

## Database ERD

```mermaid
erDiagram
  USER ||--o{ WORKSPACE : owns
  WORKSPACE ||--o{ ROOM : contains
  ROOM ||--o{ ROOM_MEMBERSHIP : has
  USER ||--o{ ROOM_MEMBERSHIP : joins
  ROOM ||--o{ MESSAGE : stores
  USER ||--o{ MESSAGE : sends
  MESSAGE ||--o{ MESSAGE : thread_reply
  MESSAGE ||--o{ MESSAGE_DELIVERY_RECEIPT : delivered
  MESSAGE ||--o{ MESSAGE_READ_RECEIPT : read
  MESSAGE ||--|| MESSAGE_RISK_SCORE : scored
  USER ||--o{ PRESENCE_SESSION : has
  USER ||--o{ AUDIT_LOG : acts
  WORKSPACE ||--o{ DIRECT_CONVERSATION : has
  ROOM ||--|| DIRECT_CONVERSATION : backs
```
