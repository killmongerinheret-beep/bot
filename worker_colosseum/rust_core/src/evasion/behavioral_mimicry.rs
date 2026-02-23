//! Behavioral mimicry for human-like interaction patterns
//! 
//! This module provides utilities to simulate human-like behavior:
//! - Mouse movement along Bezier curves
//! - Variable typing speeds with errors
//! - Random scroll patterns
//! - Human-like delays

use rand::{thread_rng, Rng, distributions::Distribution};
use std::time::Duration;

/// Point for mouse path calculation
#[derive(Clone, Copy, Debug)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Distance to another point
    pub fn distance(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }
}

/// Bezier curve for natural mouse movement
pub struct BezierCurve {
    pub start: Point,
    pub end: Point,
    pub control1: Point,
    pub control2: Point,
}

impl BezierCurve {
    /// Create a new cubic Bezier curve
    pub fn cubic(start: Point, end: Point, control1: Point, control2: Point) -> Self {
        Self {
            start,
            end,
            control1,
            control2,
        }
    }

    /// Create a natural mouse path with randomized control points
    pub fn natural_path(start: Point, end: Point) -> Self {
        let mut rng = thread_rng();
        
        // Random control points that create a slight curve
        let offset1 = rng.gen_range(-50.0..50.0);
        let offset2 = rng.gen_range(-50.0..50.0);
        
        let control1 = Point::new(
            start.x + (end.x - start.x) * 0.3 + offset1,
            start.y + (end.y - start.y) * 0.3 + offset2,
        );
        
        let control2 = Point::new(
            start.x + (end.x - start.x) * 0.7 - offset1,
            start.y + (end.y - start.y) * 0.7 - offset2,
        );

        Self::cubic(start, end, control1, control2)
    }

    /// Get point at parameter t (0.0 to 1.0)
    pub fn point_at(&self, t: f64) -> Point {
        let t2 = t * t;
        let t3 = t2 * t;
        let mt = 1.0 - t;
        let mt2 = mt * mt;
        let mt3 = mt2 * mt;

        let x = mt3 * self.start.x
            + 3.0 * mt2 * t * self.control1.x
            + 3.0 * mt * t2 * self.control2.x
            + t3 * self.end.x;

        let y = mt3 * self.start.y
            + 3.0 * mt2 * t * self.control1.y
            + 3.0 * mt * t2 * self.control2.y
            + t3 * self.end.y;

        Point::new(x, y)
    }

    /// Generate path points with velocity profile
    pub fn generate_path(&self, num_points: usize) -> Vec<(Point, f64)> {
        let mut points = Vec::with_capacity(num_points);
        
        for i in 0..num_points {
            let t = i as f64 / (num_points - 1) as f64;
            let point = self.point_at(t);
            
            // Velocity profile: slow at start and end, fast in middle
            let velocity = if t < 0.2 {
                0.5 + t * 2.5 // Acceleration
            } else if t > 0.8 {
                1.0 - (t - 0.8) * 5.0 // Deceleration
            } else {
                1.0 // Max velocity
            };
            
            points.push((point, velocity));
        }
        
        points
    }
}

/// Human-like typing simulator
pub struct TypingSimulator {
    pub base_delay_ms: u64,
    pub jitter_percent: f64,
    pub error_rate: f64,
}

impl Default for TypingSimulator {
    fn default() -> Self {
        Self {
            base_delay_ms: 100,
            jitter_percent: 0.3,
            error_rate: 0.03, // 3% typo rate
        }
    }
}

impl TypingSimulator {
    /// Simulate typing a string, returns keystrokes with delays
    pub fn simulate_typing(&self, text: &str) -> Vec<Keystroke> {
        let mut rng = thread_rng();
        let mut keystrokes = Vec::new();
        let chars: Vec<char> = text.chars().collect();
        
        let mut i = 0;
        while i < chars.len() {
            let char_to_type = chars[i];
            
            // Maybe make a typo
            if rng.gen_bool(self.error_rate) {
                // Type wrong character
                let wrong_char = self.random_adjacent_key(char_to_type);
                let delay = self.random_delay();
                keystrokes.push(Keystroke {
                    character: wrong_char,
                    delay_ms: delay,
                    action: KeyAction::Press,
                });
                
                // Pause (realization of mistake)
                keystrokes.push(Keystroke {
                    character: wrong_char,
                    delay_ms: rng.gen_range(200..500),
                    action: KeyAction::Pause,
                });
                
                // Backspace
                keystrokes.push(Keystroke {
                    character: '\x08',
                    delay_ms: rng.gen_range(50..150),
                    action: KeyAction::Backspace,
                });
                
                // Continue without advancing (retype same character)
                continue;
            }
            
            // Type correct character
            let delay = self.random_delay();
            keystrokes.push(Keystroke {
                character: char_to_type,
                delay_ms: delay,
                action: KeyAction::Press,
            });
            
            i += 1;
        }
        
        keystrokes
    }

    /// Generate random delay between keystrokes
    fn random_delay(&self) -> u64 {
        let mut rng = thread_rng();
        let jitter = self.base_delay_ms as f64 * self.jitter_percent;
        let delay = self.base_delay_ms as f64 + rng.gen_range(-jitter..jitter);
        delay.max(20.0) as u64 // Minimum 20ms
    }

    /// Get a random adjacent key (for typo simulation)
    fn random_adjacent_key(&self, c: char) -> char {
        let mut rng = thread_rng();
        let adjacent = self.get_adjacent_keys(c);
        
        if adjacent.is_empty() {
            // Fallback: random letter
            (rng.gen_range(b'a'..=b'z') as char)
        } else {
            adjacent[rng.gen_range(0..adjacent.len())]
        }
    }

    /// Get adjacent keys on QWERTY keyboard
    fn get_adjacent_keys(&self, c: char) -> Vec<char> {
        let keyboard: std::collections::HashMap<char, Vec<char>> = [
            ('a', vec!['q', 'w', 's', 'x', 'z']),
            ('b', vec!['v', 'g', 'h', 'n']),
            ('c', vec!['x', 'd', 'f', 'v']),
            ('d', vec!['s', 'e', 'r', 'f', 'c', 'x']),
            ('e', vec!['w', 's', 'd', 'r']),
            ('f', vec!['d', 'r', 't', 'g', 'v', 'c']),
            ('g', vec!['f', 't', 'y', 'h', 'b', 'v']),
            ('h', vec!['g', 'y', 'u', 'j', 'n', 'b']),
            ('i', vec!['u', 'j', 'k', 'o']),
            ('j', vec!['h', 'u', 'i', 'k', 'm', 'n']),
            ('k', vec!['j', 'i', 'o', 'l', 'm']),
            ('l', vec!['k', 'o', 'p', ';']),
            ('m', vec!['n', 'j', 'k', ',']),
            ('n', vec!['b', 'h', 'j', 'm']),
            ('o', vec!['i', 'k', 'l', 'p']),
            ('p', vec!['o', 'l', ';', '[']),
            ('q', vec!['1', '2', 'w', 'a']),
            ('r', vec!['e', 'd', 'f', 't']),
            ('s', vec!['a', 'w', 'e', 'd', 'x', 'z']),
            ('t', vec!['r', 'f', 'g', 'y']),
            ('u', vec!['y', 'h', 'j', 'i']),
            ('v', vec!['c', 'f', 'g', 'b']),
            ('w', vec!['q', 'a', 's', 'e']),
            ('x', vec!['z', 's', 'd', 'c']),
            ('y', vec!['t', 'g', 'h', 'u']),
            ('z', vec!['a', 's', 'x']),
        ].iter().cloned().collect();

        keyboard.get(&c).cloned().unwrap_or_default()
    }
}

/// Keystroke event
#[derive(Clone, Debug)]
pub struct Keystroke {
    pub character: char,
    pub delay_ms: u64,
    pub action: KeyAction,
}

/// Key action type
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum KeyAction {
    Press,
    Backspace,
    Pause, // Hesitation
}

/// Scroll behavior simulator
pub struct ScrollSimulator {
    pub base_velocity: f64,
    pub deceleration: f64,
}

impl Default for ScrollSimulator {
    fn default() -> Self {
        Self {
            base_velocity: 500.0, // pixels/second
            deceleration: 0.9,
        }
    }
}

impl ScrollSimulator {
    /// Simulate scroll to target position
    pub fn simulate_scroll(&self, target_delta: i32) -> Vec<ScrollEvent> {
        let mut rng = thread_rng();
        let mut events = Vec::new();
        let mut remaining = target_delta as f64;
        let mut velocity = self.base_velocity * (0.5 + rng.gen::<f64>());
        
        while remaining.abs() > 10.0 {
            let step = (velocity * 0.016).min(remaining.abs()) * remaining.signum();
            remaining -= step;
            
            let jitter = rng.gen_range(0.8..1.2);
            events.push(ScrollEvent {
                delta: step as i32,
                duration_ms: (16.0 * jitter) as u64,
            });
            
            velocity *= self.deceleration;
            
            // Random pause occasionally
            if rng.gen_bool(0.05) {
                events.push(ScrollEvent {
                    delta: 0,
                    duration_ms: rng.gen_range(100..300),
                });
            }
        }
        
        events
    }
}

/// Scroll event
#[derive(Clone, Debug)]
pub struct ScrollEvent {
    pub delta: i32,
    pub duration_ms: u64,
}

/// Human-like delay generator
pub struct DelayGenerator {
    pub base_ms: u64,
    pub jitter_percent: f64,
    pub distribution: DelayDistribution,
}

#[derive(Clone, Copy, Debug)]
pub enum DelayDistribution {
    Uniform,
    Normal,   // Bell curve
    Pareto,   // Long tail (human urgency pattern)
}

impl Default for DelayGenerator {
    fn default() -> Self {
        Self {
            base_ms: 1000,
            jitter_percent: 0.3,
            distribution: DelayDistribution::Pareto,
        }
    }
}

impl DelayGenerator {
    /// Generate a random delay
    pub fn generate(&self) -> Duration {
        let mut rng = thread_rng();
        
        let delay_ms = match self.distribution {
            DelayDistribution::Uniform => {
                let jitter = (self.base_ms as f64 * self.jitter_percent) as u64;
                self.base_ms + rng.gen_range(0..jitter * 2) - jitter
            }
            DelayDistribution::Normal => {
                // Simplified normal distribution
                let sum: f64 = (0..6).map(|_| rng.gen::<f64>()).sum();
                let normal = (sum / 6.0 - 0.5) * 2.0; // -1 to 1
                let jitter = self.base_ms as f64 * self.jitter_percent;
                (self.base_ms as f64 + normal * jitter) as u64
            }
            DelayDistribution::Pareto => {
                // Pareto: more short delays, occasional long ones
                let u = rng.gen::<f64>();
                let shape = 2.0;
                let scale = self.base_ms as f64;
                let pareto = scale / u.powf(1.0 / shape);
                pareto.min(self.base_ms as f64 * 3.0) as u64
            }
        };
        
        Duration::from_millis(delay_ms.max(10))
    }

    /// Generate thinking delay (between actions)
    pub fn thinking_delay(&self) -> Duration {
        let mut gen = Self {
            base_ms: self.base_ms * 2,
            ..*self
        };
        gen.generate()
    }
}

/// Complete behavioral mimicry suite
pub struct BehavioralMimicry {
    pub typing: TypingSimulator,
    pub scrolling: ScrollSimulator,
    pub delays: DelayGenerator,
}

impl Default for BehavioralMimicry {
    fn default() -> Self {
        Self {
            typing: TypingSimulator::default(),
            scrolling: ScrollSimulator::default(),
            delays: DelayGenerator::default(),
        }
    }
}

impl BehavioralMimicry {
    /// Simulate mouse movement between two points
    pub fn mouse_move(&self, from: Point, to: Point) -> Vec<(Point, Duration)> {
        let curve = BezierCurve::natural_path(from, to);
        let path = curve.generate_path(20);
        
        path.into_iter()
            .map(|(point, velocity)| {
                let delay_ms = (20.0 / velocity) as u64;
                (point, Duration::from_millis(delay_ms))
            })
            .collect()
    }

    /// Simulate page reading delay
    pub fn reading_delay(&self, content_length: usize) -> Duration {
        // Average reading speed: ~200 words per minute
        let words = content_length / 5;
        let ms_per_word = 300; // 300ms per word
        let total_ms = (words * ms_per_word) as u64;
        
        // Add randomness
        let mut rng = thread_rng();
        let with_variance = total_ms + rng.gen_range(0..total_ms / 2);
        
        Duration::from_millis(with_variance.min(30000)) // Cap at 30s
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bezier_curve() {
        let start = Point::new(0.0, 0.0);
        let end = Point::new(100.0, 100.0);
        let curve = BezierCurve::natural_path(start, end);
        
        // Start point
        let p0 = curve.point_at(0.0);
        assert!((p0.x - start.x).abs() < 0.01);
        assert!((p0.y - start.y).abs() < 0.01);
        
        // End point
        let p1 = curve.point_at(1.0);
        assert!((p1.x - end.x).abs() < 0.01);
        assert!((p1.y - end.y).abs() < 0.01);
    }

    #[test]
    fn test_typing_simulator() {
        let sim = TypingSimulator::default();
        let keystrokes = sim.simulate_typing("hello");
        
        // Should have keystrokes (might have more due to typos)
        assert!(!keystrokes.is_empty());
    }

    #[test]
    fn test_delay_generator() {
        let gen = DelayGenerator::default();
        let delay = gen.generate();
        
        assert!(delay.as_millis() >= 10);
    }
}
