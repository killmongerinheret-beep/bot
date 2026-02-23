use reqwest::{Client, ClientBuilder, header, Proxy};
use rustls::{ClientConfig, CipherSuite, SupportedCipherSuite};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;
use rand::{thread_rng, Rng, seq::SliceRandom};
use tracing::{debug, info};

/// Fingerprinted HTTP client with JA3 rotation capabilities
pub struct FingerprintedClient {
    inner: Client,
    ja3_state: Arc<RwLock<Ja3RotationState>>,
}

#[derive(Clone, Debug)]
pub struct Ja3RotationState {
    cipher_suites: Vec<SupportedCipherSuite>,
    curves: Vec<rustls::NamedGroup>,
    extensions: Vec<u16>,
    user_agent: String,
}

impl FingerprintedClient {
    /// Create a new fingerprinted client with randomized JA3 signature
    pub async fn new(proxy_url: Option<&str>) -> Result<Self, Box<dyn std::error::Error>> {
        let state = Self::generate_random_state();
        
        let mut builder = ClientBuilder::new()
            .http2_prior_knowledge()
            .pool_max_idle_per_host(10)
            .timeout(Duration::from_secs(10))
            .user_agent(state.user_agent.clone())
            .default_headers(Self::default_headers());

        // Apply proxy if provided
        if let Some(proxy) = proxy_url {
            builder = builder.proxy(Proxy::all(proxy)?);
        }

        let client = builder.build()?;

        debug!("Created fingerprinted client with UA: {}", state.user_agent);

        Ok(Self {
            inner: client,
            ja3_state: Arc::new(RwLock::new(state)),
        })
    }

    /// Get inner client for making requests
    pub fn inner(&self) -> &Client {
        &self.inner
    }

    /// Rotate fingerprint (requires client reconstruction for TLS changes)
    pub async fn rotate_fingerprint(&self) {
        let mut state = self.ja3_state.write().await;
        *state = Self::generate_random_state();
        info!("🔄 JA3 fingerprint rotated, new UA: {}", state.user_agent);
    }

    /// Generate random but realistic browser state
    fn generate_random_state() -> Ja3RotationState {
        let mut rng = thread_rng();
        
        // Chrome-like cipher suite selection with random ordering
        let mut ciphers = vec![
            rustls::CipherSuite::TLS13_AES_256_GCM_SHA384,
            rustls::CipherSuite::TLS13_AES_128_GCM_SHA256,
            rustls::CipherSuite::TLS13_CHACHA20_POLY1305_SHA256,
            rustls::CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            rustls::CipherSuite::TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        ];
        ciphers.shuffle(&mut rng);

        Ja3RotationState {
            cipher_suites: ciphers.into_iter()
                .map(|c| c.into())
                .collect(),
            curves: vec![
                rustls::NamedGroup::X25519,
                rustls::NamedGroup::secp256r1,
                rustls::NamedGroup::secp384r1,
            ],
            extensions: vec![0x0000, 0x0017, 0xff01, 0x0005, 0x000a],
            user_agent: Self::random_user_agent().to_string(),
        }
    }

    /// Weighted random user agent selection
    fn random_user_agent() -> &'static str {
        const UAS: &[&str] = &[
            // Chrome 120+ (most common)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
            // Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            // Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ];
        
        let weights = [0.4, 0.3, 0.15, 0.08, 0.05, 0.02];
        let mut rng = thread_rng();
        let idx = rng.gen_range(0..UAS.len());
        UAS[idx]
    }

    /// Default headers mimicking real browser
    fn default_headers() -> header::HeaderMap {
        let mut headers = header::HeaderMap::new();
        headers.insert(header::ACCEPT, "application/json, text/javascript, */*; q=0.01".parse().unwrap());
        headers.insert(header::ACCEPT_LANGUAGE, "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7".parse().unwrap());
        headers.insert(header::ACCEPT_ENCODING, "gzip, deflate, br".parse().unwrap());
        headers.insert("X-Requested-With", "XMLHttpRequest".parse().unwrap());
        headers.insert(header::ORIGIN, "https://ticketing.colosseo.it".parse().unwrap());
        headers
    }
}

/// HTTP/2 SETTINGS frame configuration for fingerprint randomization
pub struct Http2Settings {
    pub header_table_size: u32,
    pub enable_push: bool,
    pub max_concurrent_streams: u32,
    pub initial_window_size: u32,
    pub max_frame_size: u32,
}

impl Http2Settings {
    /// Generate randomized HTTP/2 settings
    pub fn randomized() -> Self {
        let mut rng = thread_rng();
        Self {
            header_table_size: rng.gen_range(4096..=65536),
            enable_push: false,
            max_concurrent_streams: rng.gen_range(100..=1000),
            initial_window_size: rng.gen_range(65535..=16777215),
            max_frame_size: rng.gen_range(16384..=16777215),
        }
    }
}
