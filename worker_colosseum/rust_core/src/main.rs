use std::sync::Arc;
use tokio::runtime::{Builder, Runtime};
use tracing::{info, error};

mod client;
mod parser;
mod state_machine;
mod redis_store;
mod grpc_server;
mod models;
mod evasion;

use crate::grpc_server::MonitorServer;
use crate::redis_store::StateStore;

fn create_optimized_runtime() -> Runtime {
    Builder::new_multi_thread()
        .worker_threads(num_cpus::get())
        .max_blocking_threads(512)
        .thread_stack_size(2 * 1024 * 1024) // 2MB stack
        .enable_all()
        .event_interval(61)
        .global_queue_interval(61)
        .max_io_events_per_tick(1024)
        .build()
        .expect("Failed to create tokio runtime")
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter("info,colosseo_monitor=debug")
        .with_target(false)
        .init();

    info!("🚀 Colosseo Monitor Core starting...");

    // Load configuration
    let config = load_config().await?;
    
    // Initialize Redis state store
    let state_store = Arc::new(StateStore::new(&config.redis_url).await?);
    info!("✅ Redis connection established");

    // Create optimized runtime
    let runtime = create_optimized_runtime();
    
    // Start gRPC server for orchestrator communication
    let grpc_server = MonitorServer::new(
        state_store.clone(),
        config.grpc_bind_address,
    );

    info!("📡 Starting gRPC server on {}", config.grpc_bind_address);
    
    // Run server
    grpc_server.run().await?;

    Ok(())
}

#[derive(Debug, Clone)]
struct AppConfig {
    redis_url: String,
    grpc_bind_address: String,
    max_concurrent_monitors: usize,
    default_poll_interval_ms: u64,
}

async fn load_config() -> anyhow::Result<AppConfig> {
    // TODO: Load from config file or environment
    Ok(AppConfig {
        redis_url: std::env::var("REDIS_URL")
            .unwrap_or_else(|_| "redis://localhost:6379".to_string()),
        grpc_bind_address: std::env::var("GRPC_BIND")
            .unwrap_or_else(|_| "[::1]:50051".to_string()),
        max_concurrent_monitors: 10000,
        default_poll_interval_ms: 5000,
    })
}
