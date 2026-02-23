// internal/proxy/manager.go - Dynamic proxy pool with health monitoring
package proxy

import (
	"context"
	"fmt"
	"math/rand"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

// Proxy represents a single proxy with health tracking
type Proxy struct {
	URL               *url.URL
	HealthScore       float64 // 0-1, based on success rate
	LastUsed          time.Time
	LastError         error
	ConsecutiveErrors int
	BannedUntil       time.Time
	Geographic        string // "IT", "DE", "FR", etc.
	ASN               string // ISP identifier
}

// Manager handles proxy pool with health checking
type Manager struct {
	proxies             []*Proxy
	mu                  sync.RWMutex
	healthCheckInterval time.Duration
	metrics             *prometheus.CounterVec
	testEndpoint        string
}

// NewManager creates a new proxy manager
func NewManager(proxyURLs []string, checkInterval time.Duration) (*Manager, error) {
	m := &Manager{
		proxies:             make([]*Proxy, 0, len(proxyURLs)),
		healthCheckInterval: checkInterval,
		metrics: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "proxy_requests_total",
			Help: "Total requests by proxy and status",
		}, []string{"proxy", "status"}),
		testEndpoint: "https://ticketing.colosseo.it/", // Health check endpoint
	}

	for _, u := range proxyURLs {
		parsed, err := url.Parse(u)
		if err != nil {
			return nil, fmt.Errorf("invalid proxy URL %s: %w", u, err)
		}

		m.proxies = append(m.proxies, &Proxy{
			URL:         parsed,
			HealthScore: 1.0,
			Geographic:  extractGeographic(parsed),
			ASN:         extractASN(parsed),
		})
	}

	// Start health check loop
	go m.healthCheckLoop()

	return m, nil
}

// GetProxy returns a healthy proxy with geographic preference
func (m *Manager) GetProxy(preferredGeo string) *url.URL {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// Filter healthy, non-banned proxies
	candidates := make([]*Proxy, 0)
	for _, p := range m.proxies {
		if p.BannedUntil.After(time.Now()) {
			continue
		}
		if p.HealthScore < 0.3 {
			continue
		}
		candidates = append(candidates, p)
	}

	if len(candidates) == 0 {
		// Fallback: return least recently used regardless of health
		return m.fallbackProxy()
	}

	// Weighted selection by health score and geographic preference
	var totalWeight float64
	for _, p := range candidates {
		weight := p.HealthScore
		if p.Geographic == preferredGeo {
			weight *= 2.0 // Geographic preference bonus
		}
		totalWeight += weight
	}

	r := rand.Float64() * totalWeight
	for _, p := range candidates {
		weight := p.HealthScore
		if p.Geographic == preferredGeo {
			weight *= 2.0
		}
		r -= weight
		if r <= 0 {
			p.LastUsed = time.Now()
			return p.URL
		}
	}

	return candidates[0].URL
}

// ReportResult updates proxy health based on request result
func (m *Manager) ReportResult(proxyURL *url.URL, success bool, latency time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	for _, p := range m.proxies {
		if p.URL.String() == proxyURL.String() {
			if success {
				p.ConsecutiveErrors = 0
				p.HealthScore = min(1.0, p.HealthScore*1.1+0.05)
				m.metrics.WithLabelValues(p.URL.Host, "success").Inc()
			} else {
				p.ConsecutiveErrors++
				p.HealthScore *= 0.8
				if p.ConsecutiveErrors > 5 {
					// Exponential ban time
					banDuration := time.Duration(p.ConsecutiveErrors) * time.Minute
					p.BannedUntil = time.Now().Add(banDuration)
				}
				m.metrics.WithLabelValues(p.URL.Host, "error").Inc()
			}
			break
		}
	}
}

// healthCheckLoop runs periodic health checks
func (m *Manager) healthCheckLoop() {
	ticker := time.NewTicker(m.healthCheckInterval)
	defer ticker.Stop()

	for range ticker.C {
		m.runHealthChecks()
	}
}

// runHealthChecks tests all proxies
func (m *Manager) runHealthChecks() {
	var wg sync.WaitGroup
	
	m.mu.RLock()
	proxies := make([]*Proxy, len(m.proxies))
	copy(proxies, m.proxies)
	m.mu.RUnlock()

	for _, p := range proxies {
		wg.Add(1)
		go func(proxy *Proxy) {
			defer wg.Done()

			client := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &http.Transport{
					Proxy: http.ProxyURL(proxy.URL),
				},
			}

			start := time.Now()
			resp, err := client.Get(m.testEndpoint)
			latency := time.Since(start)

			success := err == nil && resp != nil && resp.StatusCode == 200
			if resp != nil {
				resp.Body.Close()
			}

			m.ReportResult(proxy.URL, success, latency)
		}(p)
	}

	wg.Wait()
}

// fallbackProxy returns least recently used proxy
func (m *Manager) fallbackProxy() *url.URL {
	var oldest *Proxy
	for _, p := range m.proxies {
		if oldest == nil || p.LastUsed.Before(oldest.LastUsed) {
			oldest = p
		}
	}
	if oldest != nil {
		return oldest.URL
	}
	return nil
}

// GetHealthStats returns health statistics for all proxies
func (m *Manager) GetHealthStats() []ProxyHealth {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := make([]ProxyHealth, len(m.proxies))
	for i, p := range m.proxies {
		stats[i] = ProxyHealth{
			URL:         p.URL.String(),
			HealthScore: p.HealthScore,
			Geographic:  p.Geographic,
			Banned:      p.BannedUntil.After(time.Now()),
		}
	}
	return stats
}

// ProxyHealth represents proxy health statistics
type ProxyHealth struct {
	URL         string  `json:"url"`
	HealthScore float64 `json:"health_score"`
	Geographic  string  `json:"geographic"`
	Banned      bool    `json:"banned"`
}

// Helper functions
func extractGeographic(proxyURL *url.URL) string {
	// TODO: Implement IP geolocation lookup
	// For now, extract from URL if contains country code
	host := proxyURL.Hostname()
	
	// Common patterns
	if contains(host, ".it") {
		return "IT"
	}
	if contains(host, ".de") {
		return "DE"
	}
	if contains(host, ".fr") {
		return "FR"
	}
	return "Unknown"
}

func extractASN(proxyURL *url.URL) string {
	// TODO: Implement ASN lookup
	return "Unknown"
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && 
		(s == substr || 
		 len(s) > len(substr) && 
		 (s[:len(substr)] == substr || 
		  s[len(s)-len(substr):] == substr ||
		  containsInternal(s, substr)))
}

func containsInternal(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
