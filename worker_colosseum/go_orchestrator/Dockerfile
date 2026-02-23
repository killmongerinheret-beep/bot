# Multi-stage build for Go Orchestrator
FROM golang:1.21-alpine AS builder

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /app

# Copy go.mod and go.sum for caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o orchestrator \
    cmd/orchestrator/main.go

# Runtime stage
FROM scratch

# Copy certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

WORKDIR /app

# Copy binary
COPY --from=builder /app/orchestrator /usr/local/bin/

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/usr/local/bin/orchestrator", "-health-check"] || exit 1

ENTRYPOINT ["orchestrator"]
