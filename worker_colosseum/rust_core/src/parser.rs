use scraper::{Html, Selector, ElementRef};
use std::collections::HashMap;
use tracing::{debug, warn};

use crate::models::{ParsedAvailability, AvailabilityStatus, AvailabilityIndicator, Confidence};

/// High-performance HTML availability extractor
pub struct AvailabilityParser {
    selectors: Vec<(Selector, AvailabilityIndicator)>,
}

impl AvailabilityParser {
    /// Create parser with multiple selector strategies for resilience
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let selectors = vec![
            // Primary: calendar day availability
            (Selector::parse("div.calendar-day.available")?, 
             AvailabilityIndicator::Available),
            (Selector::parse("div.calendar-day.sold-out")?, 
             AvailabilityIndicator::SoldOut),
            (Selector::parse("div.calendar-day.esaurito")?, 
             AvailabilityIndicator::SoldOut),
            
            // Secondary: time slot buttons
            (Selector::parse("button.time-slot:not([disabled])")?, 
             AvailabilityIndicator::Available),
            (Selector::parse("button.time-slot[disabled]")?, 
             AvailabilityIndicator::SoldOut),
            
            // Tertiary: text-based indicators (Italian/English)
            (Selector::parse("span.disponibile")?, 
             AvailabilityIndicator::Available),
            (Selector::parse("span.esaurito")?, 
             AvailabilityIndicator::SoldOut),
            (Selector::parse("span.available")?, 
             AvailabilityIndicator::Available),
            (Selector::parse("span.sold-out")?, 
             AvailabilityIndicator::SoldOut),
            
            // Quaternary: data attributes
            (Selector::parse("[data-availability='true']")?, 
             AvailabilityIndicator::Available),
            (Selector::parse("[data-availability='false']")?, 
             AvailabilityIndicator::SoldOut),
            
            // Loading indicators
            (Selector::parse(".loading")?, 
             AvailabilityIndicator::Loading),
            (Selector::parse(".spinner")?, 
             AvailabilityIndicator::Loading),
        ];

        Ok(Self { selectors })
    }

    /// Parse HTML and extract availability information
    pub fn parse(&self, html: &str) -> ParsedAvailability {
        let document = Html::parse_document(html);
        let mut results: HashMap<String, Vec<AvailabilityIndicator>> = HashMap::new();
        let mut raw_indicators = 0;

        // Apply all selector strategies
        for (selector, indicator) in &self.selectors {
            for element in document.select(selector) {
                raw_indicators += 1;
                let key = self.extract_key(&element);
                results.entry(key)
                    .or_insert_with(Vec::new)
                    .push(indicator.clone());
            }
        }

        // Resolve consensus for each slot
        let slots: HashMap<String, AvailabilityStatus> = results
            .iter()
            .map(|(key, indicators)| {
                let status = self.resolve_consensus(indicators);
                (key.clone(), status)
            })
            .collect();

        let confidence = self.calculate_confidence(&results);

        debug!(
            "Parsed {} slots with {} raw indicators, confidence: {:.2}",
            slots.len(),
            raw_indicators,
            confidence
        );

        ParsedAvailability {
            slots,
            confidence,
            raw_indicators,
            timestamp: chrono::Utc::now(),
        }
    }

    /// Extract date/time identifier from element
    fn extract_key(&self, element: &ElementRef) -> String {
        // Try data attributes first
        let value = element.value();
        
        value.attr("data-date")
            .or_else(|| value.attr("data-time"))
            .or_else(|| value.attr("data-slot"))
            .or_else(|| value.attr("data-event-id"))
            // Try parent elements
            .or_else(|| {
                element.parent().and_then(|parent| {
                    parent.value().as_element().and_then(|el| {
                        el.attr("data-date")
                    })
                })
            })
            // Fallback to text content
            .map(|s| s.to_string())
            .unwrap_or_else(|| "unknown".to_string())
    }

    /// Resolve consensus from multiple indicators
    fn resolve_consensus(&self, indicators: &[AvailabilityIndicator]) -> AvailabilityStatus {
        let available_count = indicators.iter()
            .filter(|i| matches!(i, AvailabilityIndicator::Available))
            .count();
        
        let sold_out_count = indicators.iter()
            .filter(|i| matches!(i, AvailabilityIndicator::SoldOut))
            .count();
        
        let loading_count = indicators.iter()
            .filter(|i| matches!(i, AvailabilityIndicator::Loading))
            .count();

        // Loading takes precedence
        if loading_count > 0 {
            return AvailabilityStatus::Uncertain;
        }

        // Require at least 2 agreeing indicators for high confidence
        match (available_count, sold_out_count) {
            (a, s) if a > s && a >= 2 => 
                AvailabilityStatus::Available(Confidence::High),
            (a, s) if s > a && s >= 2 => 
                AvailabilityStatus::SoldOut(Confidence::High),
            (a, s) if a > s && a >= 1 => 
                AvailabilityStatus::Available(Confidence::Medium),
            (a, s) if s > a && s >= 1 => 
                AvailabilityStatus::SoldOut(Confidence::Medium),
            (a, s) if a > 0 || s > 0 => 
                AvailabilityStatus::Uncertain,
            _ => AvailabilityStatus::NoData,
        }
    }

    /// Calculate overall confidence score
    fn calculate_confidence(
        &self,
        results: &HashMap<String, Vec<AvailabilityIndicator>>
    ) -> f32 {
        if results.is_empty() {
            return 0.0;
        }

        let mut total_confidence = 0.0;
        let mut count = 0;

        for indicators in results.values() {
            let indicator_confidence = match indicators.len() {
                0 => 0.0,
                1 => 0.3,
                2 => 0.6,
                3 => 0.8,
                _ => 0.95,
            };
            
            // Bonus for agreement
            let agreement = if indicators.windows(2).all(|w| 
                std::mem::discriminant(&w[0]) == std::mem::discriminant(&w[1])
            ) {
                0.05
            } else {
                0.0
            };
            
            total_confidence += indicator_confidence + agreement;
            count += 1;
        }

        total_confidence / count as f32
    }

    /// Parse API JSON response (for direct endpoint consumption)
    pub fn parse_api_response(&self, json: &serde_json::Value) -> Option<ParsedAvailability> {
        let mut slots = HashMap::new();

        // Extract from typical API structure
        if let Some(result) = json.get("result") {
            for (guid, events) in result.as_object()? {
                if let Some(event_array) = events.as_array() {
                    for event in event_array {
                        let date = event.get("date")
                            .and_then(|d| d.as_str())
                            .unwrap_or(guid);
                        
                        let capacity = event.get("capacity")
                            .and_then(|c| c.as_i64());
                        
                        let needed = event.get("neededCapacity")
                            .and_then(|n| n.as_i64())
                            .unwrap_or(1);

                        let status = match capacity {
                            Some(c) if c >= needed => 
                                AvailabilityStatus::Available(Confidence::High),
                            Some(_) => AvailabilityStatus::SoldOut(Confidence::High),
                            None => AvailabilityStatus::Uncertain,
                        };

                        slots.insert(date.to_string(), status);
                    }
                }
            }
        }

        let confidence = if slots.is_empty() { 0.0 } else { 0.9 };

        Some(ParsedAvailability {
            slots,
            confidence,
            raw_indicators: 1,
            timestamp: chrono::Utc::now(),
        })
    }
}

impl Default for AvailabilityParser {
    fn default() -> Self {
        Self::new().expect("Failed to create default parser")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_available_calendar() {
        let html = r#"
            <div class="calendar-day available" data-date="2026-03-15">
                <span class="disponibile">Available</span>
            </div>
        "#;
        
        let parser = AvailabilityParser::new().unwrap();
        let result = parser.parse(html);
        
        assert!(result.confidence > 0.5);
        assert!(matches!(
            result.slots.get("2026-03-15"),
            Some(AvailabilityStatus::Available(_))
        ));
    }

    #[test]
    fn test_parse_sold_out() {
        let html = r#"
            <div class="calendar-day sold-out" data-date="2026-03-16">
                <span class="esaurito">Sold Out</span>
            </div>
        "#;
        
        let parser = AvailabilityParser::new().unwrap();
        let result = parser.parse(html);
        
        assert!(matches!(
            result.slots.get("2026-03-16"),
            Some(AvailabilityStatus::SoldOut(_))
        ));
    }
}
