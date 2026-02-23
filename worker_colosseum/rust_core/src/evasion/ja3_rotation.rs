//! JA3 fingerprint rotation for TLS client identification evasion
//! 
//! JA3 is a method for fingerprinting TLS clients based on the fields in the Client Hello packet.
//! This module implements rotation of TLS parameters to generate unique but plausible fingerprints.

use rustls::{
    CipherSuite, SupportedCipherSuite, ProtocolVersion, NamedGroup,
    SignatureScheme, ClientConfig
};
use rand::{thread_rng, Rng, seq::SliceRandom};

/// JA3 fingerprint components
#[derive(Clone, Debug)]
pub struct Ja3Fingerprint {
    /// TLS version
    pub version: ProtocolVersion,
    /// Cipher suites
    pub cipher_suites: Vec<SupportedCipherSuite>,
    /// Extensions
    pub extensions: Vec<u16>,
    /// Elliptic curves
    pub elliptic_curves: Vec<NamedGroup>,
    /// EC point formats
    pub ec_point_formats: Vec<u8>,
}

impl Ja3Fingerprint {
    /// Generate a Chrome-like fingerprint with randomization
    pub fn chrome_like() -> Self {
        let mut rng = thread_rng();
        
        // Chrome typically uses these cipher suites in various orders
        let mut ciphers = vec![
            // TLS 1.3
            CipherSuite::TLS13_AES_256_GCM_SHA384,
            CipherSuite::TLS13_AES_128_GCM_SHA256,
            CipherSuite::TLS13_CHACHA20_POLY1305_SHA256,
            // TLS 1.2
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
        ];
        
        // Shuffle cipher suites
        ciphers.shuffle(&mut rng);
        
        // Sometimes drop a cipher to create variation
        if rng.gen_bool(0.3) && ciphers.len() > 5 {
            ciphers.pop();
        }

        // Chrome extensions (GREASE values omitted for simplicity)
        let extensions = vec![
            0x0000, // server_name
            0x0017, // extended_master_secret
            0xff01, // renegotiation_info
            0x0005, // status_request
            0x000a, // supported_groups
            0x000b, // ec_point_formats
            0x0023, // session_ticket
            0x0010, // application_layer_protocol_negotiation
            0x000d, // signature_algorithms
            0x002b, // supported_versions
            0x0033, // key_share
            0x002d, // psk_key_exchange_modes
            0x001b, // compress_certificate
        ];

        let curves = vec![
            NamedGroup::X25519,
            NamedGroup::secp256r1,
            NamedGroup::secp384r1,
        ];

        Self {
            version: ProtocolVersion::TLSv1_3,
            cipher_suites: ciphers.into_iter().map(|c| c.into()).collect(),
            extensions,
            elliptic_curves: curves,
            ec_point_formats: vec![0], // uncompressed
        }
    }

    /// Generate a Firefox-like fingerprint
    pub fn firefox_like() -> Self {
        let mut rng = thread_rng();
        
        let mut ciphers = vec![
            CipherSuite::TLS13_AES_256_GCM_SHA384,
            CipherSuite::TLS13_CHACHA20_POLY1305_SHA256,
            CipherSuite::TLS13_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
            CipherSuite::TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        ];
        
        ciphers.shuffle(&mut rng);

        let extensions = vec![
            0x0005, 0x0000, 0x0017, 0x0012, 0x001b, 
            0x002b, 0x0023, 0x0033, 0x0010, 0x000d,
            0x000a, 0x0015, 0xff01, 0x000b,
        ];

        let curves = vec![
            NamedGroup::X25519,
            NamedGroup::secp256r1,
            NamedGroup::secp384r1,
            NamedGroup::secp521r1,
            NamedGroup::ffdhe2048,
            NamedGroup::ffdhe3072,
        ];

        Self {
            version: ProtocolVersion::TLSv1_3,
            cipher_suites: ciphers.into_iter().map(|c| c.into()).collect(),
            extensions,
            elliptic_curves: curves,
            ec_point_formats: vec![0],
        }
    }

    /// Generate a Safari-like fingerprint
    pub fn safari_like() -> Self {
        let ciphers = vec![
            CipherSuite::TLS13_AES_256_GCM_SHA384,
            CipherSuite::TLS13_AES_128_GCM_SHA256,
            CipherSuite::TLS13_CHACHA20_POLY1305_SHA256,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            CipherSuite::TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            CipherSuite::TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        ];

        let extensions = vec![
            0x0000, 0x0017, 0xff01, 0x0005, 0x0010,
            0x000d, 0x000a, 0x001b, 0x0023, 0x002d,
            0x0033, 0x002b,
        ];

        let curves = vec![
            NamedGroup::X25519,
            NamedGroup::secp256r1,
            NamedGroup::secp384r1,
            NamedGroup::secp521r1,
        ];

        Self {
            version: ProtocolVersion::TLSv1_3,
            cipher_suites: ciphers.into_iter().map(|c| c.into()).collect(),
            extensions,
            elliptic_curves: curves,
            ec_point_formats: vec![0],
        }
    }

    /// Generate random browser-like fingerprint
    pub fn random_browser() -> Self {
        let mut rng = thread_rng();
        match rng.gen_range(0..3) {
            0 => Self::chrome_like(),
            1 => Self::firefox_like(),
            _ => Self::safari_like(),
        }
    }

    /// Convert to rustls ClientConfig
    pub fn to_client_config(&self) -> ClientConfig {
        let mut config = ClientConfig::builder()
            .with_safe_defaults()
            .with_root_certificates(Self::root_store())
            .with_no_client_auth();

        config.cipher_suites = self.cipher_suites.clone();
        config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];

        config
    }

    /// Generate JA3 hash string for this fingerprint
    pub fn ja3_hash(&self) -> String {
        // JA3 format: SSLVersion,Ciphers,Extensions,EllipticCurves,ECPointFormats
        let version = self.version.as_u16().unwrap_or(0x0303);
        
        let ciphers = self.cipher_suites.iter()
            .map(|c| format!("{:04x}", c.suite().get_u16()))
            .collect::<Vec<_>>()
            .join("-");
        
        let extensions = self.extensions.iter()
            .map(|e| format!("{:04x}", e))
            .collect::<Vec<_>>()
            .join("-");
        
        let curves = self.elliptic_curves.iter()
            .map(|c| format!("{:04x}", c.get_u16()))
            .collect::<Vec<_>>()
            .join("-");
        
        let formats = self.ec_point_formats.iter()
            .map(|f| format!("{:02x}", f))
            .collect::<Vec<_>>()
            .join("-");

        format!("{}-{}-{}-{}-{}", version, ciphers, extensions, curves, formats)
    }

    /// Get root certificate store
    fn root_store() -> rustls::RootCertStore {
        let mut store = rustls::RootCertStore::empty();
        // Add webpki roots
        store.add_trust_anchors(
            webpki_roots::TLS_SERVER_ROOTS
                .iter()
                .map(|ta| {
                    rustls::OwnedTrustAnchor::from_subject_spki_name_constraints(
                        ta.subject,
                        ta.spki,
                        ta.name_constraints,
                    )
                })
        );
        store
    }
}

/// Rotating JA3 fingerprint manager
pub struct Ja3Rotator {
    fingerprints: Vec<Ja3Fingerprint>,
    current_index: usize,
    rotation_interval: std::time::Duration,
    last_rotation: std::time::Instant,
}

impl Ja3Rotator {
    /// Create new rotator with multiple fingerprints
    pub fn new(count: usize) -> Self {
        let fingerprints: Vec<_> = (0..count)
            .map(|_| Ja3Fingerprint::random_browser())
            .collect();

        Self {
            fingerprints,
            current_index: 0,
            rotation_interval: std::time::Duration::from_secs(300), // 5 min default
            last_rotation: std::time::Instant::now(),
        }
    }

    /// Get current fingerprint
    pub fn current(&self) -> &Ja3Fingerprint {
        &self.fingerprints[self.current_index]
    }

    /// Rotate to next fingerprint
    pub fn rotate(&mut self) -> &Ja3Fingerprint {
        self.current_index = (self.current_index + 1) % self.fingerprints.len();
        self.last_rotation = std::time::Instant::now();
        self.current()
    }

    /// Check if rotation is due
    pub fn should_rotate(&self) -> bool {
        self.last_rotation.elapsed() >= self.rotation_interval
    }

    /// Auto-rotate if needed
    pub fn auto_rotate(&mut self) -> Option<&Ja3Fingerprint> {
        if self.should_rotate() {
            Some(self.rotate())
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chrome_fingerprint() {
        let fp = Ja3Fingerprint::chrome_like();
        assert!(!fp.cipher_suites.is_empty());
        assert!(!fp.extensions.is_empty());
    }

    #[test]
    fn test_ja3_hash_format() {
        let fp = Ja3Fingerprint::chrome_like();
        let hash = fp.ja3_hash();
        // Should contain 4 dashes separating 5 components
        assert_eq!(hash.matches('-').count(), 4);
    }
}
