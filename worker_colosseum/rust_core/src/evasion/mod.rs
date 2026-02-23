//! Anti-detection and evasion techniques
//! 
//! This module provides various techniques to avoid detection by anti-bot systems:
//! - JA3/TLS fingerprint rotation
//! - HTTP/2 SETTINGS frame randomization
//! - Behavioral mimicry (mouse movements, delays)

pub mod ja3_rotation;
pub mod http2_fingerprint;
pub mod behavioral_mimicry;

pub use ja3_rotation::{Ja3Fingerprint, Ja3Rotator};
pub use http2_fingerprint::Http2Settings;
pub use behavioral_mimicry::BehavioralMimicry;
