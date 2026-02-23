# Multi-stage build for Rust Core
FROM rust:1.75-slim-bookworm as builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Cargo files for caching
COPY Cargo.toml Cargo.lock ./
COPY proto ../proto

# Create dummy main.rs for dependency caching
RUN mkdir -p src && echo "fn main() {}" > src/main.rs
RUN cargo build --release && rm -rf src

# Copy actual source code
COPY src ./src
COPY build.rs ./

# Touch main.rs to force rebuild
RUN touch src/main.rs
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy gRPC health probe
COPY --from=ghcr.io/grpc-ecosystem/grpc-health-probe:v0.4.22 /ko-app/grpc-health-probe /usr/local/bin/

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/colosseo-monitor /usr/local/bin/

# Create non-root user
RUN useradd -m -u 1000 colosseo && chown -R colosseo:colosseo /app
USER colosseo

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD grpc_health_probe -addr=localhost:50051 || exit 1

ENTRYPOINT ["colosseo-monitor"]
