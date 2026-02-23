// internal/config/manager.go - Dynamic configuration with validation
package config

import (
	"fmt"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/spf13/viper"
)

// Manager handles dynamic configuration with hot-reload
type Manager struct {
	viper     *viper.Viper
	current   *Config
	mu        sync.RWMutex
	watchers  []func(*Config)
}

// Config represents the application configuration
type Config struct {
	Version   int       `mapstructure:"version"`
	Targets   []Target  `mapstructure:"targets"`
	UpdatedAt time.Time `mapstructure:"-"`
}

// Target defines a monitoring target
type Target struct {
	Name        string            `mapstructure:"name"`
	URL         string            `mapstructure:"url"`
	TicketType  string            `mapstructure:"ticket_type"`
	Selectors   map[string]string `mapstructure:"selectors"`
	Headers     map[string]string `mapstructure:"headers"`
	Priority    int               `mapstructure:"priority"`
	Timeout     time.Duration     `mapstructure:"timeout"`
}

// NewManager creates a new configuration manager
func NewManager(configPath string) (*Manager, error) {
	v := viper.New()
	v.SetConfigFile(configPath)
	v.SetConfigType("yaml")

	// Set defaults
	v.SetDefault("poll_interval", 5*time.Second)
	v.SetDefault("max_depth", 2)
	v.SetDefault("async_threads", 4)

	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}

	m := &Manager{
		viper: v,
	}

	if err := m.load(); err != nil {
		return nil, err
	}

	// Watch for changes
	v.WatchConfig()
	v.OnConfigChange(func(e fsnotify.Event) {
		if err := m.load(); err != nil {
			// Log error but don't crash
			return
		}
		m.notifyWatchers()
	})

	return m, nil
}

// load reads and validates configuration
func (m *Manager) load() error {
	var cfg Config
	if err := m.viper.Unmarshal(&cfg); err != nil {
		return fmt.Errorf("unmarshal: %w", err)
	}

	if err := validate(&cfg); err != nil {
		return fmt.Errorf("validation: %w", err)
	}

	cfg.UpdatedAt = time.Now()

	m.mu.Lock()
	m.current = &cfg
	m.mu.Unlock()

	return nil
}

// Get returns the current configuration
func (m *Manager) Get() *Config {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.current
}

// OnChange registers a callback for configuration changes
func (m *Manager) OnChange(fn func(*Config)) {
	m.watchers = append(m.watchers, fn)
}

// notifyWatchers calls all registered callbacks
func (m *Manager) notifyWatchers() {
	cfg := m.Get()
	for _, fn := range m.watchers {
		go fn(cfg) // Async notification
	}
}

// GetViper returns the underlying viper instance
func (m *Manager) GetViper() *viper.Viper {
	return m.viper
}

// validate checks configuration validity
func validate(cfg *Config) error {
	if len(cfg.Targets) == 0 {
		return fmt.Errorf("no targets configured")
	}

	seenNames := make(map[string]bool)
	for i, t := range cfg.Targets {
		if t.URL == "" {
			return fmt.Errorf("target %d: missing URL", i)
		}
		if t.Name == "" {
			return fmt.Errorf("target %d: missing name", i)
		}
		if seenNames[t.Name] {
			return fmt.Errorf("target %d: duplicate name %s", i, t.Name)
		}
		seenNames[t.Name] = true

		// Validate selectors
		if _, ok := t.Selectors["available"]; !ok {
			return fmt.Errorf("target %s: missing 'available' selector", t.Name)
		}
		if _, ok := t.Selectors["sold_out"]; !ok {
			return fmt.Errorf("target %s: missing 'sold_out' selector", t.Name)
		}
	}

	return nil
}

// GetTarget returns a target by name
func (c *Config) GetTarget(name string) (*Target, error) {
	for _, t := range c.Targets {
		if t.Name == name {
			return &t, nil
		}
	}
	return nil, fmt.Errorf("target not found: %s", name)
}

// GetTargetsByPriority returns targets sorted by priority
func (c *Config) GetTargetsByPriority() []Target {
	// Copy to avoid modifying original
	result := make([]Target, len(c.Targets))
	copy(result, c.Targets)

	// Simple bubble sort by priority (descending)
	for i := 0; i < len(result); i++ {
		for j := i + 1; j < len(result); j++ {
			if result[j].Priority > result[i].Priority {
				result[i], result[j] = result[j], result[i]
			}
		}
	}

	return result
}
