use std::pin::Pin;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio_stream::{Stream, StreamExt};
use tonic::{Request, Response, Status};
use tracing::{debug, error, info, warn};

use crate::redis_store::StateStore;
use crate::state_machine::{TicketState, TicketType};
use crate::models::{MonitorTarget, TaskPriority};

// Generated protobuf types
pub mod proto {
    tonic::include_proto!("colosseo");
}

use proto::{
    monitor_server::{Monitor, MonitorServer as TonicMonitorServer},
    acquisition_server::{Acquisition, AcquisitionServer},
    *,
};

/// gRPC server for orchestrator communication
pub struct MonitorGrpcServer {
    state_store: Arc<StateStore>,
}

impl MonitorGrpcServer {
    pub fn new(state_store: Arc<StateStore>) -> Self {
        Self { state_store }
    }

    pub fn into_service(self) -> TonicMonitorServer<Self> {
        TonicMonitorServer::new(self)
    }
}

#[tonic::async_trait]
impl Monitor for MonitorGrpcServer {
    type StartMonitoringStream = Pin<Box<dyn Stream<Item = Result<AvailabilityEvent, Status>> + Send>>;

    async fn start_monitoring(
        &self,
        request: Request<MonitorRequest>,
    ) -> Result<Response<Self::StartMonitoringStream>, Status> {
        let req = request.into_inner();
        info!("🎯 Start monitoring request for target: {}", req.target_id);

        // Create channel for streaming events
        let (tx, rx) = mpsc::channel(100);

        // Parse ticket type
        let ticket_type = match req.ticket_type {
            1 => TicketType::Ordinario,
            2 => TicketType::FullExperienceArena,
            3 => TicketType::FullExperienceUnderground,
            4 => TicketType::ForumPassSuper,
            _ => TicketType::Ordinario,
        };

        // Initialize monitoring state
        let initial_state = TicketState::Monitoring {
            started_at: std::time::Instant::now(),
            last_check: std::time::Instant::now(),
            check_count: 0,
            target_date: req.target_date.clone(),
            ticket_type,
        };

        // Save state to Redis
        if let Err(e) = self.state_store.save_state(&req.target_id, &initial_state).await {
            error!("Failed to save state: {}", e);
            return Err(Status::internal("State save failed"));
        }

        // Start monitoring task (simplified - full implementation would spawn actual monitor)
        tokio::spawn(async move {
            // Simulate monitoring loop
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(5));
            
            loop {
                interval.tick().await;
                
                // Send heartbeat event
                let event = AvailabilityEvent {
                    target_id: req.target_id.clone(),
                    timestamp_ms: chrono::Utc::now().timestamp_millis(),
                    status: 0, // UNKNOWN
                    confidence: 0.0,
                    signals: vec![],
                    metadata: std::collections::HashMap::new(),
                    slots: vec![],
                };

                if tx.send(Ok(event)).await.is_err() {
                    warn!("Monitor stream closed for {}", req.target_id);
                    break;
                }
            }
        });

        let output_stream = tokio_stream::wrappers::ReceiverStream::new(rx);
        Ok(Response::new(Box::pin(output_stream) as Self::StartMonitoringStream))
    }

    async fn stop_monitoring(
        &self,
        request: Request<StopRequest>,
    ) -> Result<Response<StopResponse>, Status> {
        let req = request.into_inner();
        info!("🛑 Stop monitoring request for target: {}", req.target_id);

        // TODO: Implement actual stop logic
        
        Ok(Response::new(StopResponse {
            success: true,
            message: "Monitoring stopped".to_string(),
        }))
    }

    async fn get_status(
        &self,
        request: Request<StatusRequest>,
    ) -> Result<Response<StatusResponse>, Status> {
        let req = request.into_inner();
        debug!("📊 Status request for: {:?}", req.target_id);

        let mut targets = vec![];

        if req.target_id.is_empty() {
            // Return all targets (would query Redis in full implementation)
            targets.push(TargetStatus {
                target_id: "example".to_string(),
                state: 1, // MONITORING
                checks_total: 100,
                detections_total: 5,
                last_check_ms: chrono::Utc::now().timestamp_millis(),
                current_proxy: "italian-residential-1".to_string(),
                health_score: 0.95,
            });
        } else {
            // Load specific target state
            match self.state_store.load_state(&req.target_id).await {
                Ok(Some(state)) => {
                    let state_num = match state {
                        TicketState::Monitoring { .. } => 1,
                        TicketState::Detected { .. } => 2,
                        TicketState::Carting { .. } => 3,
                        TicketState::Holding { .. } => 4,
                        TicketState::Paying { .. } => 5,
                        TicketState::Confirmed { .. } => 6,
                        TicketState::Failed { .. } => 7,
                    };

                    targets.push(TargetStatus {
                        target_id: req.target_id,
                        state: state_num,
                        checks_total: 0,
                        detections_total: 0,
                        last_check_ms: chrono::Utc::now().timestamp_millis(),
                        current_proxy: "unknown".to_string(),
                        health_score: 1.0,
                    });
                }
                Ok(None) => return Err(Status::not_found("Target not found")),
                Err(e) => {
                    error!("Failed to load state: {}", e);
                    return Err(Status::internal("State load failed"));
                }
            }
        }

        Ok(Response::new(StatusResponse { targets }))
    }

    type StreamMetricsStream = Pin<Box<dyn Stream<Item = Result<MetricsEvent, Status>> + Send>>;

    async fn stream_metrics(
        &self,
        _request: Request<MetricsRequest>,
    ) -> Result<Response<Self::StreamMetricsStream>, Status> {
        let (tx, rx) = mpsc::channel(100);

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(5));
            
            loop {
                interval.tick().await;

                let event = MetricsEvent {
                    timestamp_ms: chrono::Utc::now().timestamp_millis(),
                    requests_per_second: 100.0,
                    avg_latency_ms: 50.0,
                    error_rate: 0.01,
                    proxy_health: std::collections::HashMap::new(),
                };

                if tx.send(Ok(event)).await.is_err() {
                    break;
                }
            }
        });

        let output_stream = tokio_stream::wrappers::ReceiverStream::new(rx);
        Ok(Response::new(Box::pin(output_stream) as Self::StreamMetricsStream))
    }
}

/// Acquisition service implementation
pub struct AcquisitionGrpcServer {
    state_store: Arc<StateStore>,
}

impl AcquisitionGrpcServer {
    pub fn new(state_store: Arc<StateStore>) -> Self {
        Self { state_store }
    }
}

#[tonic::async_trait]
impl Acquisition for AcquisitionGrpcServer {
    async fn initiate_acquisition(
        &self,
        request: Request<AcquisitionRequest>,
    ) -> Result<Response<AcquisitionResponse>, Status> {
        let req = request.into_inner();
        info!("🛒 Initiate acquisition for target: {}", req.target_id);

        // Try to claim cart lock
        let cart_id = format!("cart-{}", uuid::Uuid::new_v4());
        
        match self.state_store.try_claim_cart(&req.event_id, &cart_id, 900).await {
            Ok(true) => {
                info!("✅ Cart claim acquired: {}", cart_id);
                
                Ok(Response::new(AcquisitionResponse {
                    cart_id: cart_id.clone(),
                    hold_expires_ms: chrono::Utc::now().timestamp_millis() + 900_000, // 15 min
                    payment_options: vec![
                        PaymentOption {
                            method: 1,
                            display_name: "UniCredit Card".to_string(),
                            requires_3ds: true,
                        },
                        PaymentOption {
                            method: 2,
                            display_name: "PayPal".to_string(),
                            requires_3ds: false,
                        },
                    ],
                    success: true,
                    error_message: "".to_string(),
                }))
            }
            Ok(false) => {
                warn!("❌ Cart claim failed - already claimed");
                Ok(Response::new(AcquisitionResponse {
                    cart_id: "".to_string(),
                    hold_expires_ms: 0,
                    payment_options: vec![],
                    success: false,
                    error_message: "Already claimed".to_string(),
                }))
            }
            Err(e) => {
                error!("Redis error: {}", e);
                Err(Status::internal("Cart claim failed"))
            }
        }
    }

    async fn get_cart_status(
        &self,
        request: Request<CartStatusRequest>,
    ) -> Result<Response<CartStatusResponse>, Status> {
        let req = request.into_inner();
        debug!("📦 Cart status request: {}", req.cart_id);

        // TODO: Implement actual cart status retrieval

        Ok(Response::new(CartStatusResponse {
            cart_id: req.cart_id,
            state: 1, // ACTIVE
            expires_ms: chrono::Utc::now().timestamp_millis() + 600_000,
            items: vec![],
            total_cents: 0,
        }))
    }

    async fn complete_payment(
        &self,
        request: Request<PaymentRequest>,
    ) -> Result<Response<PaymentResponse>, Status> {
        let req = request.into_inner();
        info!("💳 Payment request for cart: {}", req.cart_id);

        // TODO: Implement actual payment flow

        Ok(Response::new(PaymentResponse {
            success: true,
            confirmation_code: "ABC123XYZ".to_string(),
            error_message: "".to_string(),
            state: 4, // COMPLETED
            timestamp_ms: chrono::Utc::now().timestamp_millis(),
        }))
    }

    async fn release_cart(
        &self,
        request: Request<ReleaseRequest>,
    ) -> Result<Response<ReleaseResponse>, Status> {
        let req = request.into_inner();
        info!("🔓 Release cart: {} (reason: {})", req.cart_id, req.reason);

        // TODO: Implement cart release

        Ok(Response::new(ReleaseResponse {
            success: true,
        }))
    }
}

/// Build file for protobuf generation
pub fn build() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::compile_protos("../proto/colosseo.proto")?;
    Ok(())
}
