# Colosseum Worker Architecture Transformation Plan

## Executive Summary

This document outlines the complete transformation of the `worker_colosseum` module from a basic Python script to an elite hybrid Rust+Go architecture as specified in the technical reference document.

---

## Current State Analysis

### Existing Implementation (`monitor.py`)
- **Language**: Python with curl_cffi
- **Lines of Code**: ~280
- **Architecture**: Single-threaded, synchronous
- **Features**:
  - Basic cookie caching from Redis
  - Simple GUID extraction
  - Queue-it detection (basic)
  - Exponential backoff retry
  - Proxy support

### Limitations
1. No true concurrency (blocking I/O)
2. No TLS/JA3 fingerprint rotation
3. No distributed state management
4. Basic error handling
5. No adaptive polling strategies
6. No visual confirmation pipeline
7. No sophisticated evasion techniques

---

## Target Architecture (Per PDF Specification)

### Hybrid Stack
| Component | Language | Purpose | Performance Target |
|-----------|----------|---------|-------------------|
| Core Monitor | Rust | High-frequency availability detection | Sub-100ms response |
| Orchestrator | Go | Distributed coordination, notifications | 2000+ RPS capability |
| State Store | Redis | Distributed locks, session persistence | <5ms operations |
| Payment Handler | Rust/Go | Cart injection, payment automation | <1s completion |

---

## Transformation Phases

### Phase 1: Rust Core Engine (Foundation)

#### 1.1 Project Structure
```
worker_colosseum/
├── rust_core/                    # Rust high-performance monitor
│   ├── Cargo.toml
│   ├── src/
│   │   ├── main.rs              # Entry point
│   │   ├── client.rs            # Fingerprinted HTTP client
│   │   ├── parser.rs            # HTML availability extraction
│   │   ├── state_machine.rs     # Ticket lifecycle management
│   │   ├── redis_store.rs       # Distributed coordination
│   │   ├── grpc_server.rs       # Service interface
│   │   ├── evasion/             # Anti-detection modules
│   │   │   ├── ja3_rotation.rs
│   │   │   ├── http2_fingerprint.rs
│   │   │   └── behavioral_mimicry.rs
│   │   └── models.rs            # Data structures
│   └── proto/
│       └── colosseo.proto       # gRPC definitions
├── go_orchestrator/              # Go coordination layer
│   ├── cmd/
│   │   └── orchestrator/
│   │       └── main.go
│   ├── internal/
│   │   ├── proxy/
│   │   │   └── manager.go
│   │   ├── notify/
│   │   │   └── dispatcher.go
│   │   └── config/
│   │       └── manager.go
│   └── go.mod
├── python_legacy/                # Current implementation (deprecated)
│   └── monitor.py
├── docker-compose.yml
└── README.md
```

#### 1.2 Core Rust Components

**A. Fingerprinted HTTP Client (`client.rs`)**
```rust
pub struct FingerprintedClient {
    inner: Client,
    ja3_rotation: Arc<RwLock<Ja3RotationState>>,
    http2_config: Http2Settings,
}

impl FingerprintedClient {
    pub async fn new(proxy_url: Option<&str>) -> Result<Self> {
        // JA3 fingerprint rotation via rustls
        // HTTP/2 SETTINGS frame randomization
        // Cipher suite subset selection
    }
}
```

**B. Availability Parser (`parser.rs`)**
```rust
pub struct AvailabilityParser {
    selectors: Vec<(Selector, AvailabilityIndicator)>,
}

impl AvailabilityParser {
    pub fn parse(&self, html: &str) -> ParsedAvailability {
        // Multi-strategy selector fallback
        // Consensus resolution for confidence scoring
    }
}
```

**C. State Machine (`state_machine.rs`)**
```rust
pub enum TicketState {
    Monitoring { started_at: Instant, check_count: u64 },
    Detected { detected_at: Instant, confidence: f32 },
    Carting { session_id: String, cart_id: Option<String> },
    Holding { cart_id: String, expires_at: Instant },
    Paying { payment_token: String, method: PaymentMethod },
    Confirmed { confirmation_code: String },
    Failed { reason: FailureReason, retry_eligible: bool },
}
```

#### 1.3 Key Features to Implement

| Feature | Priority | Complexity | Reference (PDF) |
|---------|----------|------------|-----------------|
| JA3/TLS fingerprint rotation | Critical | High | Section 2.1.4, 10.2.1 |
| HTTP/2 SETTINGS randomization | Critical | Medium | Section 10.2.2 |
| Adaptive polling intervals | High | Medium | Section 4.1.3 |
| Multi-signal correlation | High | High | Section 4.2.4 |
| Visual confirmation pipeline | Medium | High | Section 4.2.3 |
| Timing analysis detection | Medium | High | Section 5.3.1 |

### Phase 2: Go Orchestration Layer

#### 2.1 Components

**A. Proxy Manager (`internal/proxy/manager.go`)**
- Health score tracking per proxy
- Geographic affinity routing (Italian IPs priority)
- Automatic failover and rotation
- Ban detection with quarantine

**B. Notification Dispatcher (`internal/notify/dispatcher.go`)**
- Telegram Bot API integration
- WebSocket real-time dashboard
- Webhook external integration
- Multi-channel fallback

**C. Configuration Manager (`internal/config/manager.go`)**
- Viper-based hot-reload
- Target validation
- Dynamic reconfiguration without restart

#### 2.2 Colly Integration
```go
func createCollector(target Target) *colly.Collector {
    c := colly.NewCollector(
        colly.UserAgent(randomUserAgent()),
        colly.Async(true),
    )
    // Redis storage for session persistence
    // Proxy rotation with health checking
    // Adaptive rate limiting with jitter
}
```

### Phase 3: Hybrid Coordination

#### 3.1 gRPC Service Mesh
```protobuf
service Monitor {
    rpc StartMonitoring(MonitorRequest) returns (stream AvailabilityEvent);
    rpc StopMonitoring(StopRequest) returns (StopResponse);
}

service Acquisition {
    rpc InitiateAcquisition(AcquisitionRequest) returns (AcquisitionResponse);
    rpc CompletePayment(PaymentRequest) returns (PaymentResponse);
}
```

#### 3.2 Redis State Store
- Distributed locks for cart claims (SET NX EX)
- State machine persistence
- Metrics aggregation (time-series)
- Session coordination

---

## Implementation Roadmap

### Week 1: Foundation Setup
- [ ] Create Rust project structure with Cargo workspace
- [ ] Set up Go module with basic orchestrator skeleton
- [ ] Define protobuf schemas for gRPC communication
- [ ] Implement basic Redis connection layer

### Week 2: Rust Core - Client & Parser
- [ ] Fingerprinted HTTP client with rustls
- [ ] JA3 fingerprint rotation
- [ ] HTTP/2 SETTINGS randomization
- [ ] HTML parser with multi-selector strategy

### Week 3: Rust Core - State Machine & gRPC
- [ ] TicketState enum with transitions
- [ ] Timeout handling for each state
- [ ] gRPC server implementation
- [ ] Integration tests

### Week 4: Go Orchestrator
- [ ] Colly-based collectors
- [ ] Proxy manager with health checking
- [ ] Notification dispatcher (Telegram)
- [ ] Configuration hot-reload

### Week 5: Integration & Testing
- [ ] Rust-Go hybrid coordination
- [ ] Docker Compose deployment
- [ ] Load testing (2000+ RPS target)
- [ ] Evasion technique validation

### Week 6: Advanced Features
- [ ] Visual confirmation pipeline
- [ ] Timing analysis detection
- [ ] Parallel cart strategy
- [ ] Payment automation prep

---

## Critical Implementation Details

### 1. JA3 Fingerprint Rotation
```rust
fn build_tls_config(state: &Ja3RotationState) -> ClientConfig {
    let mut config = ClientConfig::builder()
        .with_safe_defaults()
        .with_root_certificates(root_store())
        .with_no_client_auth();
    
    // Rotate cipher suites for unique JA3 hash
    config.cipher_suites = state.cipher_suites.clone();
    config
}
```

### 2. Adaptive Polling Strategy
```rust
enum PollPhase {
    PreRelease { interval: Duration },      // 60s ±30s
    ReleaseApproach { interval: Duration }, // 10s ±5s
    ReleaseWindow { interval: Duration },   // 500ms ±250ms
    FlashDrop { interval: Duration },       // 3s ±1.5s
}
```

### 3. Multi-Signal Detection
```rust
struct DetectionSignal {
    source: SignalSource,       // API, DOM, Visual, Timing
    weight: f32,                // 0.0 - 1.0
    confidence: f32,
    timestamp: Instant,
}

// Weighted consensus: >=0.7 triggers acquisition
```

### 4. Session Warmup Sequence
```
Initial landing (5-10s) → Information gathering (15-30s) → 
Calendar exploration (20-40s) → Return visit (10-20s) → 
Acquisition ready
```

---

## Deployment Architecture

### Local (Raspberry Pi 4 Cluster)
```yaml
services:
  monitor-core:
    image: colosseo-monitor:rust-latest
    deploy:
      replicas: 4
    resources:
      limits:
        cpus: '3.0'
        memory: 2G
  
  orchestrator:
    image: colosseo-orchestrator:go-latest
    ports:
      - "8080:8080"
  
  redis:
    image: redis:7-alpine
```

### Cloud (Hetzner/OVH)
- Kubernetes with auto-scaling HPA
- Italian/EU residential proxy pools
- Prometheus/Grafana observability
- Spot instances with checkpoint recovery

---

## Performance Targets

| Metric | Current (Python) | Target (Rust+Go) | Improvement |
|--------|-----------------|------------------|-------------|
| Requests/sec | ~10-50 | 2000+ | 40-200x |
| Response parsing | ~15ms | <100µs | 150x |
| End-to-end latency | 2-5s | <100ms | 20-50x |
| Concurrent sessions | 1 | 10,000+ | 10,000x |
| Memory per session | ~50MB | ~2KB | 25,000x |

---

## Risk Mitigation

### Detection Evasion
1. **TLS/JA3 rotation**: Per-session cipher suite variation
2. **HTTP/2 fingerprinting**: SETTINGS frame randomization
3. **Behavioral mimicry**: Bezier curve mouse paths, variable delays
4. **Residential proxy rotation**: ASN diversity (5+ Italian ISPs)

### Legal/Operational
1. **Jurisdictional separation**: Control plane in non-EU
2. **Identity compartmentalization**: Per-ticket personas
3. **Log sanitization**: No persistent purchase records
4. **Rate limiting compliance**: Respect platform boundaries

---

## Success Criteria

1. ✅ Sub-100ms availability detection latency
2. ✅ 2000+ RPS sustained throughput
3. ✅ <5% false positive rate (multi-signal correlation)
4. ✅ 24/7 operation without restart (memory safety)
5. ✅ Successful cart acquisition within 15-minute hold window
6. ✅ Passes anti-bot detection (no CAPTCHA triggers)

---

## Migration Strategy

### Option A: Big Bang (Recommended for Clean Slate)
- Freeze current Python implementation
- Complete Rust+Go rewrite
- Parallel testing period
- Cutover once validation passes

### Option B: Gradual Migration
- Keep Python as fallback
- Implement Rust core incrementally
- A/B testing between implementations
- Full migration after confidence established

---

## Next Steps

1. **Approve architecture plan**
2. **Set up development environment** (Rust 1.75+, Go 1.21+)
3. **Begin Phase 1: Rust core skeleton**
4. **Weekly progress reviews**

---

*Document Version: 1.0*
*Based on: Elite Colosseo Ticket Automation System - Technical Architecture & Implementation*
