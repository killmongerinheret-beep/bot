// internal/notify/dispatcher.go - Multi-channel notification with fallback
package notify

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/gorilla/websocket"
)

// Dispatcher handles multi-channel notifications
type Dispatcher struct {
	telegram   *tgbotapi.BotAPI
	chatID     int64
	webSocket  *websocket.Conn
	webhookURL string
	fallbackCh chan<- Alert
}

// Alert represents a notification alert
type Alert struct {
	Level        AlertLevel             `json:"level"`
	Timestamp    time.Time              `json:"timestamp"`
	Target       string                 `json:"target"`
	Availability AvailabilityStatus     `json:"availability"`
	Confidence   float32                `json:"confidence"`
	Screenshot   []byte                 `json:"screenshot,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// AlertLevel represents severity level
type AlertLevel int

const (
	Info AlertLevel = iota
	Warning
	Critical
)

// AvailabilityStatus represents ticket availability
type AvailabilityStatus string

const (
	Available       AvailabilityStatus = "available"
	SoldOut         AvailabilityStatus = "sold_out"
	NotYetReleased  AvailabilityStatus = "not_yet_released"
	Uncertain       AvailabilityStatus = "uncertain"
)

// NewDispatcher creates a new notification dispatcher
func NewDispatcher(
	telegramBot *tgbotapi.BotAPI,
	chatID int64,
	webhookURL string,
) *Dispatcher {
	return &Dispatcher{
		telegram:   telegramBot,
		chatID:     chatID,
		webhookURL: webhookURL,
	}
}

// SetWebSocket sets the WebSocket connection for real-time updates
func (d *Dispatcher) SetWebSocket(ws *websocket.Conn) {
	d.webSocket = ws
}

// SetFallbackChannel sets the fallback channel for failed notifications
func (d *Dispatcher) SetFallbackChannel(ch chan<- Alert) {
	d.fallbackCh = ch
}

// Dispatch sends alert through all configured channels
func (d *Dispatcher) Dispatch(ctx context.Context, alert Alert) error {
	var errs []error

	// Primary: Telegram for critical and warning alerts
	if alert.Level >= Warning {
		if err := d.sendTelegram(alert); err != nil {
			errs = append(errs, fmt.Errorf("telegram: %w", err))
		}
	}

	// Secondary: WebSocket for real-time dashboard
	if d.webSocket != nil {
		if err := d.sendWebSocket(alert); err != nil {
			errs = append(errs, fmt.Errorf("websocket: %w", err))
		}
	}

	// Tertiary: Webhook for external integration
	if d.webhookURL != "" {
		if err := d.sendWebhook(alert); err != nil {
			errs = append(errs, fmt.Errorf("webhook: %w", err))
		}
	}

	// Fallback: channel-based for internal handling
	if len(errs) > 0 && d.fallbackCh != nil {
		select {
		case d.fallbackCh <- alert:
		default: // Non-blocking
		}
	}

	if len(errs) == 3 { // All channels failed
		return fmt.Errorf("all notification channels failed: %v", errs)
	}

	return nil
}

// sendTelegram sends alert via Telegram Bot API
func (d *Dispatcher) sendTelegram(alert Alert) error {
	if d.telegram == nil {
		return fmt.Errorf("telegram bot not configured")
	}

	var msg string
	switch alert.Level {
	case Critical:
		msg = fmt.Sprintf(
			"🚨 *CRITICAL: Tickets Available*\n\n"+
				"📍 Target: %s\n"+
				"⏰ Time: %s\n"+
				"🎯 Confidence: %.0f%%\n"+
				"📊 Status: %s",
			escapeMarkdown(alert.Target),
			alert.Timestamp.Format("15:04:05.000"),
			alert.Confidence*100,
			alert.Availability,
		)

	case Warning:
		msg = fmt.Sprintf(
			"⚠️ *WARNING: Possible Availability*\n\n"+
				"📍 Target: %s\n"+
				"🎯 Confidence: %.0f%%",
			escapeMarkdown(alert.Target),
			alert.Confidence*100,
		)

	default:
		msg = fmt.Sprintf(
			"ℹ️ Info: %s - %s",
			alert.Target,
			alert.Availability,
		)
	}

	// Include screenshot if available and critical
	if alert.Level == Critical && len(alert.Screenshot) > 0 {
		photo := tgbotapi.NewPhoto(d.chatID, tgbotapi.FileBytes{
			Name: "confirmation.png",
			Bytes: alert.Screenshot,
		})
		photo.Caption = msg
		photo.ParseMode = "Markdown"
		_, err := d.telegram.Send(photo)
		return err
	}

	tgMsg := tgbotapi.NewMessage(d.chatID, msg)
	tgMsg.ParseMode = "Markdown"
	tgMsg.DisableWebPagePreview = true

	_, err := d.telegram.Send(tgMsg)
	return err
}

// sendWebSocket sends alert via WebSocket
func (d *Dispatcher) sendWebSocket(alert Alert) error {
	if d.webSocket == nil {
		return fmt.Errorf("websocket not connected")
	}

	data, err := json.Marshal(alert)
	if err != nil {
		return err
	}

	return d.webSocket.WriteMessage(websocket.TextMessage, data)
}

// sendWebhook sends alert via HTTP webhook
func (d *Dispatcher) sendWebhook(alert Alert) error {
	if d.webhookURL == "" {
		return fmt.Errorf("webhook URL not configured")
	}

	data, err := json.Marshal(alert)
	if err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "POST", d.webhookURL, bytes.NewReader(data))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("webhook returned %d", resp.StatusCode)
	}

	return nil
}

// escapeMarkdown escapes Markdown special characters
func escapeMarkdown(text string) string {
	chars := []rune{'_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'}
	result := []rune(text)
	
	for i := 0; i < len(result); i++ {
		for _, char := range chars {
			if result[i] == char {
				result = append(result[:i], append([]rune{'\\', char}, result[i+1:]...)...)
				i++
				break
			}
		}
	}
	
	return string(result)
}
