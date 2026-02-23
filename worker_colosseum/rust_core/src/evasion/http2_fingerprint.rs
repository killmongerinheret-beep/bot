//! HTTP/2 SETTINGS frame fingerprint randomization
//! 
//! HTTP/2 clients can be fingerprinted by the parameters they send in the SETTINGS frame.
//! This module implements randomization of these parameters to evade fingerprinting.

use rand::{thread_rng, Rng};

/// HTTP/2 SETTINGS parameters
#[derive(Clone, Debug)]
pub struct Http2Settings {
    /// HEADER_TABLE_SIZE (default: 4096)
    pub header_table_size: u32,
    
    /// ENABLE_PUSH (default: 1)
    pub enable_push: bool,
    
    /// MAX_CONCURRENT_STREAMS (default: unlimited)
    pub max_concurrent_streams: u32,
    
    /// INITIAL_WINDOW_SIZE (default: 65535)
    pub initial_window_size: u32,
    
    /// MAX_FRAME_SIZE (default: 16384)
    pub max_frame_size: u32,
    
    /// MAX_HEADER_LIST_SIZE (default: unlimited)
    pub max_header_list_size: Option<u32>,
}

impl Http2Settings {
    /// Create settings mimicking Chrome
    pub fn chrome() -> Self {
        let mut rng = thread_rng();
        
        Self {
            header_table_size: rng.gen_range(65536..=131072),
            enable_push: false, // Chrome disables push
            max_concurrent_streams: rng.gen_range(100..=1000),
            initial_window_size: rng.gen_range(6291456..=16777216), // 6MB - 16MB
            max_frame_size: 16384, // Chrome uses default
            max_header_list_size: None,
        }
    }

    /// Create settings mimicking Firefox
    pub fn firefox() -> Self {
        let mut rng = thread_rng();
        
        Self {
            header_table_size: rng.gen_range(65536..=262144),
            enable_push: true,
            max_concurrent_streams: rng.gen_range(100..=250),
            initial_window_size: rng.gen_range(131072..=1048576), // 128KB - 1MB
            max_frame_size: 16384,
            max_header_list_size: None,
        }
    }

    /// Create settings mimicking Safari
    pub fn safari() -> Self {
        let mut rng = thread_rng();
        
        Self {
            header_table_size: rng.gen_range(4096..=65536),
            enable_push: true,
            max_concurrent_streams: 100,
            initial_window_size: rng.gen_range(65535..=262144),
            max_frame_size: 16384,
            max_header_list_size: None,
        }
    }

    /// Create randomized but plausible settings
    pub fn randomized() -> Self {
        let mut rng = thread_rng();
        let browser = rng.gen_range(0..3);
        
        match browser {
            0 => Self::chrome(),
            1 => Self::firefox(),
            _ => Self::safari(),
        }
    }

    /// Create settings with fully randomized parameters
    pub fn fully_random() -> Self {
        let mut rng = thread_rng();
        
        Self {
            header_table_size: rng.gen_range(4096..=16777216),
            enable_push: rng.gen_bool(0.5),
            max_concurrent_streams: rng.gen_range(1..=1000),
            initial_window_size: rng.gen_range(65535..=16777215),
            max_frame_size: rng.gen_range(16384..=16777215),
            max_header_list_size: if rng.gen_bool(0.5) {
                Some(rng.gen_range(1024..=16777216))
            } else {
                None
            },
        }
    }

    /// Convert to hyper HTTP/2 settings
    pub fn to_hyper_settings(&self) -> hyper::client::Http2Config {
        // This would integrate with hyper's HTTP/2 configuration
        // Implementation depends on hyper version
        unimplemented!("Hyper integration requires specific version configuration")
    }

    /// Generate SETTINGS frame bytes
    pub fn to_frame_bytes(&self) -> Vec<u8> {
        let mut frame = Vec::new();
        
        // SETTINGS frame header (9 bytes)
        // Length (3 bytes) - will calculate
        // Type (1 byte) = 0x4 for SETTINGS
        // Flags (1 byte) = 0x0
        // Stream ID (4 bytes) = 0x0
        
        let mut payload = Vec::new();
        
        // Settings pairs (2 bytes identifier + 4 bytes value)
        // HEADER_TABLE_SIZE (0x1)
        payload.extend_from_slice(&0x0001u16.to_be_bytes());
        payload.extend_from_slice(&self.header_table_size.to_be_bytes());
        
        // ENABLE_PUSH (0x2)
        payload.extend_from_slice(&0x0002u16.to_be_bytes());
        let push_val: u32 = if self.enable_push { 1 } else { 0 };
        payload.extend_from_slice(&push_val.to_be_bytes());
        
        // MAX_CONCURRENT_STREAMS (0x3)
        payload.extend_from_slice(&0x0003u16.to_be_bytes());
        payload.extend_from_slice(&self.max_concurrent_streams.to_be_bytes());
        
        // INITIAL_WINDOW_SIZE (0x4)
        payload.extend_from_slice(&0x0004u16.to_be_bytes());
        payload.extend_from_slice(&self.initial_window_size.to_be_bytes());
        
        // MAX_FRAME_SIZE (0x5)
        payload.extend_from_slice(&0x0005u16.to_be_bytes());
        payload.extend_from_slice(&self.max_frame_size.to_be_bytes());
        
        // MAX_HEADER_LIST_SIZE (0x6) - optional
        if let Some(max) = self.max_header_list_size {
            payload.extend_from_slice(&0x0006u16.to_be_bytes());
            payload.extend_from_slice(&max.to_be_bytes());
        }
        
        // Frame header
        let length = payload.len() as u32;
        frame.extend_from_slice(&length.to_be_bytes()[1..4]); // 3 bytes
        frame.push(0x04); // Type: SETTINGS
        frame.push(0x00); // Flags: none
        frame.extend_from_slice(&0x00000000u32.to_be_bytes()); // Stream ID: 0
        
        // Payload
        frame.extend_from_slice(&payload);
        
        frame
    }

    /// Calculate HTTP/2 fingerprint hash
    /// This is used by some detection systems to identify clients
    pub fn fingerprint_hash(&self) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        self.header_table_size.hash(&mut hasher);
        self.enable_push.hash(&mut hasher);
        self.max_concurrent_streams.hash(&mut hasher);
        self.initial_window_size.hash(&mut hasher);
        self.max_frame_size.hash(&mut hasher);
        self.max_header_list_size.hash(&mut hasher);
        
        format!("{:016x}", hasher.finish())
    }
}

impl Default for Http2Settings {
    fn default() -> Self {
        Self::randomized()
    }
}

/// Rotating HTTP/2 settings manager
pub struct Http2Rotator {
    settings: Vec<Http2Settings>,
    current_index: usize,
}

impl Http2Rotator {
    /// Create new rotator with predefined settings
    pub fn new(count: usize) -> Self {
        let settings: Vec<_> = (0..count)
            .map(|_| Http2Settings::randomized())
            .collect();

        Self {
            settings,
            current_index: 0,
        }
    }

    /// Get current settings
    pub fn current(&self) -> &Http2Settings {
        &self.settings[self.current_index]
    }

    /// Rotate to next settings
    pub fn rotate(&mut self) -> &Http2Settings {
        self.current_index = (self.current_index + 1) % self.settings.len();
        self.current()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chrome_settings() {
        let settings = Http2Settings::chrome();
        assert!(!settings.enable_push); // Chrome disables push
        assert!(settings.initial_window_size >= 6291456);
    }

    #[test]
    fn test_frame_bytes() {
        let settings = Http2Settings::chrome();
        let frame = settings.to_frame_bytes();
        
        // Frame should have at least header (9 bytes) + some settings
        assert!(frame.len() > 9);
        
        // First byte of type should be 0x04 (SETTINGS)
        assert_eq!(frame[3], 0x04);
    }

    #[test]
    fn test_fingerprint_hash() {
        let settings1 = Http2Settings::chrome();
        let settings2 = Http2Settings::chrome();
        
        // Same settings should produce same hash
        assert_eq!(
            settings1.fingerprint_hash(),
            settings1.fingerprint_hash()
        );
        
        // Different settings likely produce different hashes
        // (but could theoretically collide)
        assert_ne!(
            settings1.fingerprint_hash(),
            settings2.fingerprint_hash()
        );
    }
}
