use std::time::{Duration, Instant};
use serde::{Serialize, Deserialize};
use tracing::{debug, info, warn};

/// Complete ticket acquisition lifecycle state machine
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum TicketState {
    /// Monitoring phase - actively polling for availability
    Monitoring {
        started_at: Instant,
        last_check: Instant,
        check_count: u64,
        target_date: String,
        ticket_type: TicketType,
    },
    
    /// Detection phase - availability detected, confidence assessment
    Detected {
        detected_at: Instant,
        confidence: f32,
        signals: Vec<DetectionSignal>,
        target_date: String,
        ticket_type: TicketType,
    },
    
    /// Carting phase - initiating cart injection
    Carting {
        started_at: Instant,
        session_id: String,
        cart_id: Option<String>,
        target_date: String,
        ticket_type: TicketType,
    },
    
    /// Holding phase - cart secured, maintaining hold
    Holding {
        cart_id: String,
        expires_at: Instant,
        heartbeat_due: Instant,
        target_date: String,
        ticket_type: TicketType,
    },
    
    /// Payment phase - processing payment
    Paying {
        started_at: Instant,
        payment_token: String,
        method: PaymentMethod,
        cart_id: String,
    },
    
    /// Terminal: Confirmed - purchase complete
    Confirmed {
        confirmed_at: Instant,
        confirmation_code: String,
        tickets: Vec<TicketDetail>,
    },
    
    /// Terminal: Failed - error occurred
    Failed {
        failed_at: Instant,
        reason: FailureReason,
        retry_eligible: bool,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum TicketType {
    Ordinario,
    FullExperienceArena,
    FullExperienceUnderground,
    ForumPassSuper,
}

impl std::fmt::Display for TicketType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TicketType::Ordinario => write!(f, "Ordinario"),
            TicketType::FullExperienceArena => write!(f, "Full Experience Arena"),
            TicketType::FullExperienceUnderground => write!(f, "Full Experience Underground"),
            TicketType::ForumPassSuper => write!(f, "Forum Pass Super"),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PaymentMethod {
    UniCreditCard,
    PayPal,
    BankTransfer,
    VirtualCard { provider: String },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DetectionSignal {
    pub source: SignalSource,
    pub confidence: f32,
    pub timestamp: Instant,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum SignalSource {
    ApiResponse,
    DomMutation,
    VisualConfirmation,
    TimingAnalysis,
    CrossSession,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TicketDetail {
    pub ticket_id: String,
    pub visitor_name: String,
    pub date: String,
    pub time_slot: String,
    pub ticket_type: TicketType,
    pub price_tier: PriceTier,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PriceTier {
    Intero,    // Full price
    Ridotto,   // Reduced (EU 18-25, seniors)
    Gratuito,  // Free (under 18, disabled)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum FailureReason {
    CartHoldExpired,
    PaymentDeclined,
    SessionInvalid,
    QueueItDetected,
    RateLimited,
    NetworkError,
    ValidationFailed,
    InventoryGone,
    Timeout,
}

impl TicketState {
    /// Check if state transition is valid
    pub fn can_transition(&self, to: &TicketState) -> bool {
        use TicketState::*;
        
        matches!((self, to),
            // Monitoring → Detection
            (Monitoring{..}, Detected{..}) |
            // Detection → Carting
            (Detected{..}, Carting{..}) |
            // Carting → Holding or Failed
            (Carting{..}, Holding{..}) |
            (Carting{..}, Failed{..}) |
            // Holding → Paying or Failed
            (Holding{..}, Paying{..}) |
            (Holding{..}, Failed{..}) |
            // Paying → Confirmed or Failed
            (Paying{..}, Confirmed{..}) |
            (Paying{..}, Failed{..}) |
            // Failed (retry eligible) → Monitoring or Carting
            (Failed{retry_eligible: true, ..}, Monitoring{..}) |
            (Failed{retry_eligible: true, ..}, Carting{..})
        )
    }

    /// Get timeout duration for current state
    pub fn timeout(&self) -> Option<Duration> {
        use TicketState::*;
        
        match self {
            Monitoring{..} => Some(Duration::from_secs(86400)), // 24h max
            Detected{..} => Some(Duration::from_secs(5)),       // 5s to initiate cart
            Carting{..} => Some(Duration::from_secs(10)),       // 10s to secure hold
            Holding{expires_at, ..} => Some(*expires_at - Instant::now()),
            Paying{..} => Some(Duration::from_secs(60)),        // 60s for payment
            _ => None, // Terminal states
        }
    }

    /// Check if state has timed out
    pub fn is_timed_out(&self) -> bool {
        match self.timeout() {
            Some(timeout) => timeout <= Duration::ZERO,
            None => false,
        }
    }

    /// Transition to new state with validation
    pub fn transition(self, new_state: TicketState) -> Result<TicketState, StateTransitionError> {
        if !self.can_transition(&new_state) {
            return Err(StateTransitionError::InvalidTransition {
                from: format!("{:?}", self),
                to: format!("{:?}", new_state),
            });
        }

        info!(
            "State transition: {:?} → {:?}",
            std::mem::discriminant(&self),
            std::mem::discriminant(&new_state)
        );

        Ok(new_state)
    }

    /// Get current ticket type if applicable
    pub fn ticket_type(&self) -> Option<&TicketType> {
        use TicketState::*;
        
        match self {
            Monitoring{ticket_type, ..} |
            Detected{ticket_type, ..} |
            Carting{ticket_type, ..} |
            Holding{ticket_type, ..} => Some(ticket_type),
            _ => None,
        }
    }

    /// Get target date if applicable
    pub fn target_date(&self) -> Option<&String> {
        use TicketState::*;
        
        match self {
            Monitoring{target_date, ..} |
            Detected{target_date, ..} |
            Carting{target_date, ..} |
            Holding{target_date, ..} => Some(target_date),
            _ => None,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum StateTransitionError {
    #[error("Invalid state transition from {from} to {to}")]
    InvalidTransition { from: String, to: String },
    
    #[error("State has timed out")]
    Timeout,
    
    #[error("State serialization failed: {0}")]
    SerializationError(String),
}

/// State machine manager for tracking multiple concurrent acquisitions
pub struct StateMachineManager {
    states: std::collections::HashMap<String, TicketState>,
}

impl StateMachineManager {
    pub fn new() -> Self {
        Self {
            states: std::collections::HashMap::new(),
        }
    }

    pub fn get(&self, id: &str) -> Option<&TicketState> {
        self.states.get(id)
    }

    pub fn insert(&mut self, id: String, state: TicketState) {
        self.states.insert(id, state);
    }

    pub fn update(&mut self, id: &str, new_state: TicketState) -> Result<(), StateTransitionError> {
        if let Some(current) = self.states.remove(id) {
            let validated = current.transition(new_state)?;
            self.states.insert(id.to_string(), validated);
            Ok(())
        } else {
            Err(StateTransitionError::InvalidTransition {
                from: "None".to_string(),
                to: format!("{:?}", new_state),
            })
        }
    }

    /// Clean up terminal states
    pub fn cleanup_terminal(&mut self) {
        let terminal: Vec<_> = self.states
            .iter()
            .filter(|(_, state)| matches!(state, 
                TicketState::Confirmed{..} | TicketState::Failed{..}
            ))
            .map(|(id, _)| id.clone())
            .collect();
        
        for id in terminal {
            self.states.remove(&id);
            debug!("Cleaned up terminal state for {}", id);
        }
    }
}

impl Default for StateMachineManager {
    fn default() -> Self {
        Self::new()
    }
}
