"""
Enhanced Click-and-Sniff Method with Language Dropdown Handling

Key Insight from User Recording:
- Tickets #1 and #8: Standard tickets (no language selector)
- Tickets #2-7, 9-10: Guided tours (require language selection)

The bot must:
1. Click the ticket button
2. Check if a language dropdown appears ([data-cy='visitLang'])
3. If yes, try all languages (ENG, ITA, FRA, DEU, SPA) until slots found
4. If no, directly intercept the API response
"""

async def check_via_click_enhanced(self, page, ticket_id, ticket_name, ticket_index):
    """
    ENHANCED: Handles both standard tickets AND guided tours with language selection
    
    Args:
        ticket_id: The ticket ID to check
        ticket_name: Human-readable name
        ticket_index: Position in list (1-based) to detect if language needed
        
    Returns:
        Dict with slots and detected language (if applicable)
    """
    logger.info(f"🖱️ Clicking '{ticket_name}' (ID: {ticket_id}, Index: {ticket_index})...")
    
    # Tickets that DON'T need language selection (based on user observation)
    STANDARD_TICKET_INDICES = [1, 8]
    
    try:
        # 1. Click the ticket button
        btn = page.locator(f"[data-cy='bookTicket_{ticket_id}']")
        await btn.scroll_into_view_if_needed()
        
        if await btn.is_disabled():
            logger.warning(f"⚠️ Button disabled for {ticket_id}")
            return {"slots": [], "language": None}
        
        await btn.click()
        await page.wait_for_timeout(1000)  # Let modal load
        
        # 2. Check if language dropdown exists
        lang_dropdown = page.locator("[data-cy='visitLang']")
        has_language_selector = await lang_dropdown.count() > 0
        
        if has_language_selector and ticket_index not in STANDARD_TICKET_INDICES:
            logger.info(f"   🌐 Language selector detected - trying languages...")
            
            # Try each language
            languages_to_try = ["ENG", "ITA", "FRA", "DEU", "SPA"]
            
            for lang in languages_to_try:
                try:
                    # Click dropdown
                    await lang_dropdown.click()
                    await page.wait_for_timeout(500)
                    
                    # Select language (languages are in divs, typically div:nth-of-type(N))
                    # ENG=1, ITA=2, FRA=3, DEU=4, SPA=5 (usually)
                    lang_index = languages_to_try.index(lang) + 1
                    lang_option = page.locator(f"app-ticket-visit-language div:nth-of-type({lang_index})")
                    
                    # Setup listener BEFORE clicking
                    async with page.expect_response(
                        lambda r: "timeavail" in r.url and r.status == 200,
                        timeout=3000
                    ) as response_info:
                        await lang_option.click()
                    
                    # Check response
                    response = await response_info.value
                    data = await response.json()
                    
                    time_slots = data.get("timetable", [])
                    available = [t['time'] for t in time_slots if t.get('availability') != 'SOLD_OUT']
                    
                    if available:
                        logger.info(f"   ✅ Found {len(available)} slots for {lang}")
                        await page.keyboard.press("Escape")
                        return {"slots": available, "language": lang}
                    else:
                        logger.info(f"   ❌ No slots for {lang}")
                    
                except Exception as e:
                    logger.debug(f"   Language {lang} check failed: {e}")
                    continue
            
            # No language had slots
            logger.info(f"   ❌ No slots in any language")
            await page.keyboard.press("Escape")
            return {"slots": [], "language": None}
            
        else:
            # Standard ticket - no language selection needed
            logger.info(f"   📋 Standard ticket (no language selector)")
            
            async with page.expect_response(
                lambda r: "timeavail" in r.url and r.status == 200,
                timeout=5000
            ) as response_info:
                pass  # Already clicked the button above
            
            response = await response_info.value
            data = await response.json()
            
            time_slots = data.get("timetable", [])
            available = [t['time'] for t in time_slots if t.get('availability') != 'SOLD_OUT']
            
            await page.keyboard.press("Escape")
            
            if available:
                logger.info(f"   ✅ Found {len(available)} slots")
                return {"slots": available, "language": None}
            else:
                logger.info(f"   ❌ No slots available")
                return {"slots": [], "language": None}
            
    except Exception as e:
        logger.error(f"⚠️ Check failed: {e}")
        try:
            await page.keyboard.press("Escape")
        except:
            pass
        return {"slots": [], "language": None}
