package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gocolly/colly/v2"
	"github.com/gocolly/colly/v2/extensions"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/redis/go-redis/v9"
	"github.com/spf13/viper"
)

// MonitorConfig holds all configuration
type MonitorConfig struct {
	Targets      []Target      `mapstructure:"targets"`
	ProxyPool    ProxyConfig   `mapstructure:"proxy_pool"`
	Telegram     TelegramConfig `mapstructure:"telegram"`
	PollInterval time.Duration `mapstructure:"poll_interval"`
	MaxDepth     int           `mapstructure:"max_depth"`
	AsyncThreads int           `mapstructure:"async_threads"`
	Redis        RedisConfig   `mapstructure:"redis"`
	MetricsPort  int           `mapstructure:"metrics_port"`
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

// ProxyConfig for proxy pool management
type ProxyConfig struct {
	URLs            []string      `mapstructure:"urls"`
	HealthInterval  time.Duration `mapstructure:"health_interval"`
	RotationPolicy  string        `mapstructure:"rotation_policy"`
}

// TelegramConfig for notifications
type TelegramConfig struct {
	BotToken string `mapstructure:"bot_token"`
	ChatID   int64  `mapstructure:"chat_id"`
}

// RedisConfig for state store
type RedisConfig struct {
	Address  string `mapstructure:"address"`
	Password string `mapstructure:"password"`
	DB       int    `mapstructure:"db"`
}

var (
	// Prometheus metrics
	pollAttempts = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "colosseo_poll_attempts_total",
			Help: "Total poll attempts by target",
		},
		[]string{"target"},
	)
	
	availabilityEvents = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "colosseo_availability_events_total",
			Help: "Availability detection events",
		},
		[]string{"target", "status"},
	)
	
	acquisitions = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "colosseo_acquisitions_total",
			Help: "Acquisition attempts and results",
		},
		[]string{"status"},
	)
	
	proxyErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "colosseo_proxy_errors_total",
			Help: "Proxy errors by reason",
		},
		[]string{"reason"},
	)
)

func init() {
	prometheus.MustRegister(pollAttempts, availabilityEvents, acquisitions, proxyErrors)
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Configuration setup
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("/etc/colosseo/")
	viper.AddConfigPath("$HOME/.colosseo")

	// Environment variable overrides
	viper.BindEnv("telegram.bot_token", "TELEGRAM_BOT_TOKEN")
	viper.BindEnv("redis.address", "REDIS_URL")

	if err := viper.ReadInConfig(); err != nil {
		log.Fatalf("Config error: %v", err)
	}

	var cfg MonitorConfig
	if err := viper.Unmarshal(&cfg); err != nil {
		log.Fatalf("Config unmarshal error: %v", err)
	}

	// Hot reload
	viper.OnConfigChange(func(e fsnotify.Event) {
		log.Printf("Config changed: %s", e.Name)
		var newCfg MonitorConfig
		if err := viper.Unmarshal(&newCfg); err != nil {
			log.Printf("Failed to reload config: %v", err)
			return
		}
		// Apply new configuration
		updateConfig(&cfg, &newCfg)
	})
	viper.WatchConfig()

	log.Println("🚀 Colosseo Orchestrator starting...")

	// Initialize components
	redisClient := initRedis(cfg.Redis)
	defer redisClient.Close()
	log.Println("✅ Redis connected")

	telegramBot := initTelegram(cfg.Telegram)
	log.Println("✅ Telegram bot initialized")

	// Start metrics server
	go startMetricsServer(cfg.MetricsPort)
	log.Printf("📊 Metrics server on :%d/metrics", cfg.MetricsPort)

	// Create collectors
	collectors := make(map[string]*colly.Collector)
	for _, target := range cfg.Targets {
		collectors[target.Name] = createCollector(target, cfg, redisClient)
	}

	// Start monitoring loops
	var wg sync.WaitGroup
	for name, collector := range collectors {
		wg.Add(1)
		go runMonitor(ctx, &wg, name, collector, findTarget(cfg.Targets, name), telegramBot)
	}

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	
	log.Println("👂 Listening for signals...")
	<-sigChan
	
	log.Println("🛑 Shutting down...")
	cancel()
	wg.Wait()
	log.Println("✅ Shutdown complete")
}

func initRedis(cfg RedisConfig) *redis.Client {
	client := redis.NewClient(&redis.Options{
		Addr:     cfg.Address,
		Password: cfg.Password,
		DB:       cfg.DB,
	})
	
	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if err := client.Ping(ctx).Err(); err != nil {
		log.Fatalf("Redis connection failed: %v", err)
	}
	
	return client
}

func initTelegram(cfg TelegramConfig) *tgbotapi.BotAPI {
	if cfg.BotToken == "" {
		log.Println("⚠️ No Telegram bot token configured")
		return nil
	}
	
	bot, err := tgbotapi.NewBotAPI(cfg.BotToken)
	if err != nil {
		log.Printf("Telegram bot init failed: %v", err)
		return nil
	}
	
	log.Printf("✅ Telegram bot authorized: %s", bot.Self.UserName)
	return bot
}

func createCollector(target Target, cfg MonitorConfig, redisClient *redis.Client) *colly.Collector {
	c := colly.NewCollector(
		colly.UserAgent(randomUserAgent()),
		colly.AllowedDomains("ticketing.colosseo.it", "www.colosseo.it"),
		colly.MaxDepth(cfg.MaxDepth),
		colly.Async(true),
	)

	// Storage for session persistence
	c.SetStorage(&RedisStorage{
		client: redisClient,
		prefix: fmt.Sprintf("colly:%s:", target.Name),
	})

	// Extensions
	extensions.RandomUserAgent(c)
	extensions.Referer(c)

	// Rate limiting with adaptive jitter
	c.Limit(&colly.LimitRule{
		DomainGlob:  "*colosseo.it*",
		Parallelism: cfg.AsyncThreads,
		Delay:       cfg.PollInterval,
		RandomDelay: cfg.PollInterval / 2,
	})

	// Custom headers
	for k, v := range target.Headers {
		key, val := k, v // capture loop vars
		c.OnRequest(func(r *colly.Request) {
			r.Headers.Set(key, val)
		})
	}

	// Callbacks
	c.OnHTML(target.Selectors["available"], func(e *colly.HTMLElement) {
		handleAvailability(e, target, true)
	})
	
	c.OnHTML(target.Selectors["sold_out"], func(e *colly.HTMLElement) {
		handleAvailability(e, target, false)
	})
	
	c.OnError(func(r *colly.Response, err error) {
		handleError(r, err, target)
	})

	return c
}

func runMonitor(
	ctx context.Context,
	wg *sync.WaitGroup,
	name string,
	c *colly.Collector,
	target Target,
	bot *tgbotapi.BotAPI,
) {
	defer wg.Done()

	ticker := time.NewTicker(target.Timeout)
	defer ticker.Stop()

	log.Printf("👁️ Starting monitor: %s (interval: %v)", name, target.Timeout)

	for {
		select {
		case <-ctx.Done():
			log.Printf("🛑 Stopping monitor: %s", name)
			return
			
		case <-ticker.C:
			pollAttempts.WithLabelValues(name).Inc()
			
			if err := c.Visit(target.URL); err != nil {
				log.Printf("[%s] Visit error: %v", name, err)
			}
			c.Wait()
		}
	}
}

func handleAvailability(e *colly.HTMLElement, target Target, available bool) {
	status := "unavailable"
	if available {
		status = "available"
		log.Printf("🎉 AVAILABILITY DETECTED: %s", target.Name)
		
		// Send Telegram notification
		// TODO: Implement notification
	}
	
	availabilityEvents.WithLabelValues(target.Name, status).Inc()
}

func handleError(r *colly.Response, err error, target Target) {
	log.Printf("[%s] Error: %v (status: %d)", target.Name, err, r.StatusCode)
	
	switch r.StatusCode {
	case 429:
		proxyErrors.WithLabelValues("rate_limited").Inc()
	case 403:
		proxyErrors.WithLabelValues("banned").Inc()
	case 503:
		proxyErrors.WithLabelValues("unavailable").Inc()
	default:
		proxyErrors.WithLabelValues("other").Inc()
	}
}

func startMetricsServer(port int) {
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})
	
	addr := fmt.Sprintf(":%d", port)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Metrics server failed: %v", err)
	}
}

func randomUserAgent() string {
	uas := []string{
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
	}
	return uas[time.Now().UnixNano()%int64(len(uas))]
}

func findTarget(targets []Target, name string) Target {
	for _, t := range targets {
		if t.Name == name {
			return t
		}
	}
	return Target{}
}

func updateConfig(old, new *MonitorConfig) {
	// Atomic update of config values
	old.PollInterval = new.PollInterval
	old.AsyncThreads = new.AsyncThreads
	// Deep copy targets if needed
	log.Println("Configuration updated")
}
