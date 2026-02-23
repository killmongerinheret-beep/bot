use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Target configuration for monitoring
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MonitorTarget {
    pub id: String,
    pub name: String,
    pub url: String,
    pub ticket_type: TicketType,
    pub priority: TaskPriority,
    pub selectors: HashMap<String, String>,
    pub headers: HashMap<String, String>,
    pub poll_config: PollConfig,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum TaskPriority {
    Critical,  // T-30 releases, maximum resources
    High,      // T-7 releases
    Normal,    // Background monitoring
    Low,       // Opportunistic
}

impl TaskPriority {
    pub fn semaphore_permits(&self) -> usize {
        match self {
            TaskPriority::Critical => 100,
            TaskPriority::High => 50,
            TaskPriority::Normal => 20,
            TaskPriority::Low => 10,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PollConfig {
    pub base_interval_ms: u64,
    pub jitter_percent: u8,
    pub adaptive: bool,
}

impl Default for PollConfig {
    fn default() -> Self {
        Self {
            base_interval_ms: 5000,
            jitter_percent: 30,
            adaptive: true,
        }
    }
}

/// Availability detection result
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ParsedAvailability {
    pub slots: HashMap<String, AvailabilityStatus>,
    pub confidence: f32,
    pub raw_indicators: usize,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum AvailabilityStatus {
    Available(Confidence),
    SoldOut(Confidence),
    NotYetReleased,
    Uncertain,
    NoData,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Confidence {
    High,
    Medium,
    Low,
}

/// Detection indicators from HTML parsing
#[derive(Clone, Debug)]
pub enum AvailabilityIndicator {
    Available,      // Green highlight, "Disponibile"
    SoldOut,        // "Esaurito", grayed out
    NotYetReleased, // "Non disponibile" without date
    Loading,        // Spinner, skeleton UI
}

/// Time slot information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeSlot {
    pub time: String,
    pub available_count: u32,
    pub held_count: u32,
    pub price_tiers: HashMap<String, PriceTierInfo>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceTierInfo {
    pub cents: u32,
    pub available: u32,
}

/// Cart information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Cart {
    pub cart_id: String,
    pub expires_at: chrono::DateTime<chrono::Utc>,
    pub items: Vec<CartItem>,
    pub total_cents: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CartItem {
    pub event_id: String,
    pub date: String,
    pub time_slot: String,
    pub ticket_type: String,
    pub quantity: u32,
    pub price_tier: String,
    pub unit_price_cents: u32,
}

/// Proxy configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProxyConfig {
    pub url: String,
    pub geographic: String,
    pub asn: String,
    pub health_score: f64,
}

/// Notification alert
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Alert {
    pub level: AlertLevel,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub target: String,
    pub availability: AvailabilityStatus,
    pub confidence: f32,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, PartialOrd)]
pub enum AlertLevel {
    Info,
    Warning,
    Critical,
}

use crate::state_machine::TicketType;
