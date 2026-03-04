# Vatican Ticket ID Discovery

## Critical Finding: IDs Are Static Per Ticket Type!

### Analysis Results (March 3, 2026)

Tested 30 dates (March 4 - April 1, 2026):
- **March 4-18**: No tickets released yet
- **March 19-20**: Tickets available ✅
- **March 21+**: No tickets released yet

### ID Consistency Discovery

**The same ticket type uses the SAME ID across all dates!**

#### March 19, 2026 IDs:
- `1934042052` - Ingresso AREE MUSEALI Singoli
- `1703438231` - Ingresso AREE MUSEALI - Gruppi
- `2022918202` - Ingresso Terrazze Panoramiche 360°
- `833874468` - ESCLUSIVA! Visita con l'Esperto Storico dell'Arte
- `1472834410` - Ingresso con Audioguida
- `1011626768` - Underground Experience

#### March 20, 2026 IDs:
- `459172131` - Musei Vaticani - Biglietti d'ingresso ⭐
- `2037374249` - Musei Vaticani - Visite Guidate Singoli Musei ⭐
- `1078934336` - Musei Vaticani - Visite Guidate Gruppi Musei

### Implications

1. **No need to scrape every time** - IDs are reusable
2. **Can cache IDs globally** - Not date-specific
3. **Only need cookies** - JSESSIONID is the only dynamic part
4. **Faster checks** - Skip page navigation, go straight to API

### New Strategy

Instead of:
```
Navigate → Extract IDs → Match by name → Call API
```

We can do:
```
Get cookies → Use cached ID → Call API
```

### Known Working IDs (as of March 3, 2026)

```python
VATICAN_TICKET_IDS = {
    # Standard tickets
    "Musei Vaticani - Biglietti d'ingresso": "459172131",
    "Ingresso AREE MUSEALI Singoli": "1934042052",
    
    # Guided tours
    "Musei Vaticani - Visite Guidate Singoli Musei": "2037374249",
    "Musei Vaticani - Visite Guidate Gruppi Musei": "1078934336",
    
    # Special tickets
    "Ingresso Terrazze Panoramiche 360°": "2022918202",
    "Ingresso con Audioguida": "1472834410",
    "Underground Experience": "1011626768",
}
```

### Caveat

IDs may change when Vatican updates their system, but they appear stable for weeks/months at a time.

**Recommendation**: 
- Use cached IDs as primary method
- Fall back to page scraping if API returns 500 error
- Refresh cache weekly or on error
