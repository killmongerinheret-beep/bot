#!/usr/bin/env python3
"""Fix ticket name extraction to wait for Angular to load"""

# Fix god_tier_monitor.py
with open('/app/worker_vatican/god_tier_monitor.py', 'r') as f:
    content = f.read()

# Find and replace the ID extraction JavaScript
old_js = '''                # Extract ticket IDs
                ids = await page.evaluate("""
                    () => {
                        const results = [];
                        const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
                        buttons.forEach(btn => {
                            const id = btn.getAttribute("data-cy").split("_")[1];
                            let container = btn.closest('div.card') || btn.closest('div.row') || btn.parentElement?.parentElement;
                            let title = "Unknown";
                            if (container) {
                                const titleEl = container.querySelector('h1, h2, h3, h4, .card-title, .muvaTicketTitle');
                                if (titleEl) title = titleEl.innerText.trim();
                            }
                            results.push({id: id, name: title});
                        });
                        return results;
                    }
                """)'''

new_js = '''                # Wait for Angular to render ticket titles
                try:
                    await page.wait_for_selector('.muvaTicketTitle, [class*="ticket"], .ticket-title', timeout=5000)
                except:
                    logger.warning("⚠️ Ticket titles not loaded within 5s, proceeding anyway")
                
                # Additional wait for Angular rendering
                await page.wait_for_timeout(2000)
                
                # Extract ticket IDs with better name detection
                ids = await page.evaluate("""
                    () => {
                        const results = [];
                        const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
                        buttons.forEach(btn => {
                            const id = btn.getAttribute("data-cy").split("_")[1];
                            let title = "Unknown";
                            
                            // Strategy 1: Look in parent containers
                            let container = btn.closest('div.card, div.row, .ticket-item, [class*="ticket"]');
                            if (!container) container = btn.parentElement?.parentElement?.parentElement;
                            
                            if (container) {
                                // Try multiple selectors for title
                                const selectors = [
                                    '.muvaTicketTitle',
                                    '[class*="TicketTitle"]',
                                    '[class*="ticket-title"]',
                                    '.ticket-name',
                                    'h1', 'h2', 'h3', 'h4', 'h5',
                                    '.title',
                                    '.name',
                                    '[class*="title"]'
                                ];
                                for (let sel of selectors) {
                                    const el = container.querySelector(sel);
                                    if (el && el.innerText && el.innerText.trim().length > 3) {
                                        title = el.innerText.trim();
                                        break;
                                    }
                                }
                            }
                            
                            // Strategy 2: Look for adjacent text nodes or sibling elements
                            if (title === "Unknown") {
                                const parent = btn.parentElement;
                                if (parent) {
                                    // Check previous siblings
                                    let sibling = parent.previousElementSibling;
                                    while (sibling && title === "Unknown") {
                                        if (sibling.innerText && sibling.innerText.trim().length > 3) {
                                            title = sibling.innerText.trim().substring(0, 100);
                                            break;
                                        }
                                        sibling = sibling.previousElementSibling;
                                    }
                                }
                            }
                            
                            results.push({id: id, name: title});
                        });
                        return results;
                    }
                """)'''

content = content.replace(old_js, new_js)

with open('/app/worker_vatican/god_tier_monitor.py', 'w') as f:
    f.write(content)

print("✅ Fixed ticket name extraction")
print("   - Added wait for Angular to render titles")
print("   - Multiple selector strategies for finding names")
print("   - Fallback to sibling element text")
