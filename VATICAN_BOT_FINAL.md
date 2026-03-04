# Vatican Bot - Final Implementation

## ✅ Production Ready - 24/7 Operation

### Key Features

1. **Session Caching with JSESSIONID**
   - IDs are stable with the same JSESSIONID
   - Cache IDs and JSESSIONID together
   - Reuse for multiple checks (every 30 seconds)
   - Only refresh when session expires or API fails

2. **Optimized API Calls**
   - Standard tickets: Direct API call with `visitLang=""`
   - Guided tours: Try each language (ENG/ITA/FRA/DEU/SPA) with `visitLang={LANG}`
   - No clicking required - pure API calls
   - Fast and efficient

3. **Robust Retry Logic**
   - Up to 3 retry attempts with fresh session regeneration
   - Automatic session refresh on API errors
   - Comprehensive error handling for 24/7 reliability
   - Never crashes - always returns a result

4. **Ticket Filtering**
   - Standard tickets: Only "Musei Vaticani - Biglietti d'ingresso"
   - Skips guided tours, Palazzo Papale, and other ticket types
   - Pre-filtering before checking for efficiency

### Flow Diagram

```
1. Check if cached IDs exist with matching JSESSIONID
   ├─ YES → Use cached IDs (fast path)
   └─ NO  → Navigate to deep link and extract fresh IDs

2. For each ticket:
   ├─ Standard ticket → Call API with visitLang=""
   └─ Guided tour    → Try each language (ENG/ITA/FRA/DEU/SPA)

3. If API returns error (500):
   ├─ Retry 1: Force refresh session and IDs
   ├─ Retry 2: Force refresh again
   └─ Retry 3: Final attempt

4. Return results:
   ├─ Success: Available slots
   ├─ Sold out: No slots
   └─ Error: Logged but doesn't crash
```

### API Endpoints

**Standard Tickets:**
```
/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ID}&visitorNum={NUM}&visitDate={DD/MM/YYYY}
```

**Guided Tours:**
```
/api/visit/timeavail?lang=it&visitLang=ENG&visitTypeId={ID}&visitorNum={NUM}&visitDate={DD/MM/YYYY}
```

### Deep Link Format

```
https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp}/{slug}/1
```

- Standard tickets: `slug = "MV-Biglietti"`
- Guided tours: `slug = "MV-Visite-Guidate"`
- Timestamp: Midnight in Rome timezone (milliseconds)

### Error Handling

1. **Browser/Page Errors**: Caught and logged, returns error status
2. **API Errors (500)**: Triggers retry with fresh session
3. **Network Errors**: Caught and logged, doesn't crash
4. **Timeout Errors**: Handled gracefully with fallback
5. **Unexpected Errors**: Comprehensive try-catch blocks

### Performance

- **First check**: ~15-20 seconds (navigate + extract IDs)
- **Subsequent checks**: ~2-3 seconds (use cached IDs)
- **Retry on error**: ~15-20 seconds (regenerate session)

### Testing

Run production readiness test:
```bash
python test_production_ready.py
```

Expected output:
- ✅ Session caching verified
- ✅ ID reuse verified
- ✅ Force refresh verified
- ✅ Standard tickets working
- ✅ Guided tours working
- ✅ Error handling verified

### Deployment

The bot is ready for 24/7 operation with:
- Automatic session management
- Robust error recovery
- No manual intervention required
- Comprehensive logging for monitoring

### Monitoring

Check logs for:
- `✅ Using cached IDs` - Session reuse working
- `🔄 Force refresh requested` - Session regenerated
- `⚠️ API call failed` - Retry triggered
- `❌ Error` - Issues that need attention

### Success Metrics

- ✅ No crashes in 24/7 operation
- ✅ Automatic recovery from errors
- ✅ Fast checks with session caching
- ✅ Accurate availability detection
- ✅ Proper ticket filtering
