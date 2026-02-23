use redis::{aio::MultiplexedConnection, AsyncCommands, RedisResult};
use std::time::Duration;
use tracing::{debug, error, info};

use crate::state_machine::{TicketState, StateTransitionError};
use crate::models::Alert;

/// Distributed state store using Redis
pub struct StateStore {
    conn: MultiplexedConnection,
    key_prefix: String,
}

impl StateStore {
    /// Create new state store connection
    pub async fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        let client = redis::Client::open(redis_url)?;
        let conn = client.get_multiplexed_async_connection().await?;
        
        info!("✅ Connected to Redis at {}", redis_url);
        
        Ok(Self {
            conn,
            key_prefix: "colosseo:".to_string(),
        })
    }

    // === Cart Claim Coordination ===

    /// Try to claim a cart for a specific event (distributed lock)
    /// Returns true if claim was successful
    pub async fn try_claim_cart(
        &self,
        event_id: &str,
        cart_id: &str,
        ttl_secs: u64,
    ) -> RedisResult<bool> {
        let key = format!("{}cart_claim:{}", self.key_prefix, event_id);
        
        // NX: only set if not exists, EX: expire after ttl_secs
        let result: Option<String> = self.conn.clone()
            .set_nx_ex(&key, cart_id, ttl_secs as usize)
            .await?;
        
        let claimed = result.is_some();
        if claimed {
            debug!("✅ Cart claim acquired for event {}", event_id);
        } else {
            debug!("❌ Cart claim failed for event {} (already claimed)", event_id);
        }
        
        Ok(claimed)
    }

    /// Release cart claim
    pub async fn release_claim(&self, event_id: &str) -> RedisResult<()> {
        let key = format!("{}cart_claim:{}", self.key_prefix, event_id);
        self.conn.clone().del(&key).await?;
        debug!("🔓 Cart claim released for event {}", event_id);
        Ok(())
    }

    // === State Machine Persistence ===

    /// Save state machine state to Redis
    pub async fn save_state(
        &self,
        target_id: &str,
        state: &TicketState,
    ) -> Result<(), StateStoreError> {
        let key = format!("{}state:{}", self.key_prefix, target_id);
        
        let value = serde_json::to_string(state)
            .map_err(|e| StateStoreError::Serialization(e.to_string()))?;
        
        // 1 hour TTL for state
        self.conn.clone()
            .set_ex(&key, value, 3600)
            .await
            .map_err(StateStoreError::Redis)?;
        
        debug!("💾 State saved for target {}", target_id);
        Ok(())
    }

    /// Load state machine state from Redis
    pub async fn load_state(&self, target_id: &str) -> Result<Option<TicketState>, StateStoreError> {
        let key = format!("{}state:{}", self.key_prefix, target_id);
        
        let value: Option<String> = self.conn.clone()
            .get(&key)
            .await
            .map_err(StateStoreError::Redis)?;
        
        match value {
            Some(v) => {
                let state: TicketState = serde_json::from_str(&v)
                    .map_err(|e| StateStoreError::Deserialization(e.to_string()))?;
                debug!("📂 State loaded for target {}", target_id);
                Ok(Some(state))
            }
            None => Ok(None),
        }
    }

    // === Session Management ===

    /// Save session cookies for reuse
    pub async fn save_session(
        &self,
        session_id: &str,
        cookies: &str,
        ttl_secs: u64,
    ) -> RedisResult<()> {
        let key = format!("{}session:{}", self.key_prefix, session_id);
        self.conn.clone()
            .set_ex(&key, cookies, ttl_secs as usize)
            .await?;
        debug!("🍪 Session saved: {}", session_id);
        Ok(())
    }

    /// Load session cookies
    pub async fn load_session(&self, session_id: &str) -> RedisResult<Option<String>> {
        let key = format!("{}session:{}", self.key_prefix, session_id);
        self.conn.clone().get(&key).await
    }

    // === Metrics Aggregation ===

    /// Record metric with time-series storage
    pub async fn record_metric(
        &self,
        name: &str,
        value: f64,
        labels: &[(&str, &str)],
    ) -> RedisResult<()> {
        let label_str = labels
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join(",");
        
        let key = format!("{}metric:{}:{}", self.key_prefix, name, label_str);
        let timestamp = chrono::Utc::now().timestamp_millis();
        
        // Add to sorted set by timestamp
        let mut conn = self.conn.clone();
        conn.zadd(&key, timestamp, value.to_string()).await?;
        
        // Trim to last 24 hours
        let cutoff = timestamp - 86400000;
        conn.zremrangebyscore(&key, 0, cutoff).await?;
        
        Ok(())
    }

    /// Get metrics for time range
    pub async fn get_metrics(
        &self,
        name: &str,
        labels: &[(&str, &str)],
        since_ms: i64,
    ) -> RedisResult<Vec<(i64, f64)>> {
        let label_str = labels
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join(",");
        
        let key = format!("{}metric:{}:{}", self.key_prefix, name, label_str);
        
        let results: Vec<(i64, f64)> = self.conn.clone()
            .zrangebyscore_withscores(&key, since_ms, "+inf")
            .await?
            .into_iter()
            .filter_map(|(ts, val): (String, f64)| {
                val.to_string().parse::<f64>().ok().map(|v| (ts, v))
            })
            .collect();
        
        Ok(results)
    }

    // === Alert Queue ===

    /// Push alert to notification queue
    pub async fn queue_alert(&self, alert: &Alert) -> Result<(), StateStoreError> {
        let key = format!("{}alerts", self.key_prefix);
        let value = serde_json::to_string(alert)
            .map_err(|e| StateStoreError::Serialization(e.to_string()))?;
        
        self.conn.clone()
            .lpush(&key, value)
            .await
            .map_err(StateStoreError::Redis)?;
        
        info!("🔔 Alert queued: {:?} for {}", alert.level, alert.target);
        Ok(())
    }

    /// Pop alert from queue (for notification workers)
    pub async fn dequeue_alert(&self) -> Result<Option<Alert>, StateStoreError> {
        let key = format!("{}alerts", self.key_prefix);
        
        let value: Option<String> = self.conn.clone()
            .rpop(&key, None)
            .await
            .map_err(StateStoreError::Redis)?;
        
        match value {
            Some(v) => {
                let alert: Alert = serde_json::from_str(&v)
                    .map_err(|e| StateStoreError::Deserialization(e.to_string()))?;
                Ok(Some(alert))
            }
            None => Ok(None),
        }
    }

    // === Proxy Health ===

    /// Update proxy health score
    pub async fn update_proxy_health(
        &self,
        proxy_url: &str,
        success: bool,
        latency_ms: u64,
    ) -> RedisResult<()> {
        let key = format!("{}proxy:{}", self.key_prefix, proxy_url);
        let mut conn = self.conn.clone();
        
        if success {
            conn.hincr(&key, "success_count", 1).await?;
        } else {
            conn.hincr(&key, "error_count", 1).await?;
        }
        
        conn.hset(&key, "last_used", chrono::Utc::now().to_rfc3339()).await?;
        conn.hset(&key, "last_latency_ms", latency_ms.to_string()).await?;
        
        // Set expiration
        conn.expire(&key, 86400).await?; // 24h
        
        Ok(())
    }

    /// Get proxy health stats
    pub async fn get_proxy_health(&self, proxy_url: &str) -> RedisResult<ProxyHealth> {
        let key = format!("{}proxy:{}", self.key_prefix, proxy_url);
        let mut conn = self.conn.clone();
        
        let data: std::collections::HashMap<String, String> = conn.hgetall(&key).await?;
        
        let success_count = data.get("success_count")
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        let error_count = data.get("error_count")
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        let last_latency_ms = data.get("last_latency_ms")
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        
        let health_score = if success_count + error_count > 0 {
            success_count as f64 / (success_count + error_count) as f64
        } else {
            1.0
        };
        
        Ok(ProxyHealth {
            proxy_url: proxy_url.to_string(),
            health_score,
            success_count,
            error_count,
            last_latency_ms,
        })
    }
}

#[derive(Debug, Clone)]
pub struct ProxyHealth {
    pub proxy_url: String,
    pub health_score: f64,
    pub success_count: u64,
    pub error_count: u64,
    pub last_latency_ms: u64,
}

#[derive(Debug, thiserror::Error)]
pub enum StateStoreError {
    #[error("Redis error: {0}")]
    Redis(#[from] redis::RedisError),
    
    #[error("Serialization failed: {0}")]
    Serialization(String),
    
    #[error("Deserialization failed: {0}")]
    Deserialization(String),
    
    #[error("State transition error: {0}")]
    StateTransition(#[from] StateTransitionError),
}
