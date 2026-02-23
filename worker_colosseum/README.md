# Colosseum Worker - Elite Ticket Automation System

> **Architecture**: Hybrid Rust Core + Go Orchestrator  
> **Based on**: Elite Colosseo Ticket Automation System Technical Specification

## Architecture Overview

This module implements a high-performance, distributed ticket monitoring and acquisition system for the Colosseum ticketing platform.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Colosseum Worker                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐      ┌─────────────────────────────────────┐  │
│  │   Go Orchestrator   │      │         Rust Core Engine             │  │
│  │  ┌───────────────┐  │      │  ┌───────────────────────────────┐  │  │
│  │  │ Proxy Manager │◄─┼──────┼──┤ Fingerprinted HTTP Client     │  │  │
│  │  │ - Health check│  │      │  │ - JA3 rotation                │  │  │
│  │  │ - Rotation    │  │      │  │ - HTTP/2 randomization        │  │  │
│  │  └───────────────┘  │      │  └───────────────────────────────┘  │  │
│  │  ┌───────────────┐  │      │  ┌───────────────────────────────┐  │  │
│  │  │ Notification  │◄─┼──────┼──┤ Availability Parser           │  │  │
│  │  │ - Telegram    │  │      │  │ - Multi-selector consensus    │  │  │
│  │  │ - WebSocket   │  │      │  │ - Visual confirmation         │  │  │
│  │  └───────────────┘  │      │  └───────────────────────────────┘  │  │
│  │  ┌───────────────┐  │      │  ┌───────────────────────────────┐  │  │
│  │  │ Config Mgmt   │◄─┼──────┼──┤ State Machine                 │  │  │
│  │  │ - Hot reload  │  │      │  │ - Ticket lifecycle            │  │  │
│  │  │ - Validation  │  │      │  │ - Timeout handling            │  │  │
│  │  └───────────────┘  │      │  └───────────────────────────────┘  │  │
│  └─────────────────────┘      └─────────────────────────────────────┘  │
│           │                                    │                        │
│           └────────────┬───────────────────────┘                        │
│                        ▼                                                │
│              ┌──────────────────┐                                       │
│              │  Redis State     │                                       │
│              │  - Cart claims   │                                       │
│              │  - Session store │                                       │
│              │  - Metrics       │                                       │
│              └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Redis 7+
- (Optional) Telegram Bot Token for notifications

### Running with Docker Compose

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="your-bot-token"
export GRAFANA_PASSWORD="admin"

# Start all services
docker-compose up -d

# Scale monitor cores
docker-compose up -d --scale monitor-core=8
```

### Building from Source

**Rust Core:**
```bash
cd rust_core
cargo build --release
RUST_LOG=debug cargo run
```

**Go Orchestrator:**
```bash
cd go_orchestrator
go build -o orchestrator cmd/orchestrator/main.go
./orchestrator
```

## Configuration

Copy `go_orchestrator/config.example.yaml` to `config/config.yaml` and customize:

```yaml
targets:
  - name: "colosseo-arena-target-date"
    url: "https://ticketing.colosseo.it/en/event/parco-colosseo-24h/"
    ticket_type: "FULL_EXPERIENCE_ARENA"
    priority: 10  # Higher = more resources
    selectors:
      available: "div.calendar-day.available"
      sold_out: "div.calendar-day.sold-out"
```

## API (gRPC)

The Rust core exposes gRPC services for:

- `StartMonitoring` - Begin monitoring a target
- `StopMonitoring` - Stop monitoring
- `InitiateAcquisition` - Add tickets to cart
- `CompletePayment` - Process payment

See `proto/colosseo.proto` for full API definition.

## Performance Targets

| Metric | Python (Legacy) | Rust+Go (Target) | Improvement |
|--------|----------------|------------------|-------------|
| Requests/sec | ~50 | 2000+ | 40x |
| Response parsing | ~15ms | <100µs | 150x |
| Memory/session | ~50MB | ~2KB | 25,000x |
| Concurrent sessions | 1 | 10,000+ | 10,000x |

## Key Features

### 1. JA3/TLS Fingerprint Rotation
- Per-session cipher suite variation
- Unique but plausible browser fingerprints
- Evades TLS fingerprinting detection

### 2. Adaptive Polling
- Release window awareness (T-30, T-7, T-1)
- Jittered intervals (500ms - 60s)
- Defensive response adaptation

### 3. Multi-Signal Detection
- API response parsing
- DOM mutation observation
- Visual confirmation (screenshot diff)
- Timing analysis
- Cross-session verification

### 4. Distributed State Management
- Redis-backed state machine
- Distributed cart claim locks
- Session persistence across restarts

## Directory Structure

```
worker_colosseum/
├── rust_core/           # High-performance monitor
│   ├── src/
│   │   ├── client.rs    # Fingerprinted HTTP client
│   │   ├── parser.rs    # HTML availability parser
│   │   ├── state_machine.rs
│   │   ├── evasion/     # Anti-detection techniques
│   │   └── grpc_server.rs
│   └── Cargo.toml
├── go_orchestrator/     # Coordination layer
│   ├── cmd/
│   │   └── orchestrator/main.go
│   └── internal/
│       ├── proxy/       # Proxy pool management
│       ├── notify/      # Notification dispatcher
│       └── config/      # Hot-reload config
├── proto/               # gRPC definitions
├── python_legacy/       # Original implementation
└── docker-compose.yml
```

## Monitoring

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (admin/admin)
- **Metrics Endpoint**: `http://localhost:8080/metrics`

Key metrics:
- `colosseo_poll_attempts_total`
- `colosseo_availability_events_total`
- `colosseo_acquisitions_total`
- `colosseo_proxy_errors_total`

## Legal Notice

This system is designed for **personal use only**. The 2025 Italian Antitrust ruling (€7M fine to CoopCulture, €13M to tour operators) established liability for:
- Platform operators with inadequate bot protection
- Commercial operators using automation for resale

Personal automation for individual/family ticket acquisition carries substantially lower regulatory risk than commercial resale operations.

## License

Private - For authorized use only.
