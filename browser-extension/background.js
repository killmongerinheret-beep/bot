// Vatican Ticket Monitor - Background Service Worker
// Handles periodic checking and notifications

const VATICAN_BASE = 'https://tickets.museivaticani.va';
const ALARM_NAME = 'vaticanMonitor';

// Initialize
chrome.runtime.onInstalled.addListener(() => {
  console.log('Vatican Ticket Monitor installed');
  chrome.storage.local.set({ 
    results: [], 
    availableSlots: [],
    monitorConfig: { isActive: false }
  });
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startMonitoring') {
    startMonitoring(message.config);
  } else if (message.action === 'stopMonitoring') {
    stopMonitoring();
  } else if (message.action === 'startBackendListener') {
    startBackendListener(message.config);
  }
});

// Listen for alarms
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) {
    checkAvailability();
  }
});

// Start monitoring
async function startMonitoring(config) {
  console.log('Starting monitoring:', config);
  
  if (config.monitorMode === 'tab') {
    // Tab-based monitoring: Open Vatican tab and reload it periodically
    await startTabMonitoring(config);
  } else {
    // API-based monitoring: Background checks via alarms
    await startApiMonitoring(config);
  }
}

// API-based monitoring (original method)
async function startApiMonitoring(config) {
  // Chrome alarms have ~1 minute minimum precision
  // For intervals < 60 seconds, use a different approach
  if (config.checkInterval < 60) {
    console.warn('Intervals < 60s may not work reliably with alarms. Consider tab reload mode.');
  }
  
  // Create alarm for periodic checks (minimum 1 minute)
  const intervalMinutes = Math.max(config.checkInterval / 60, 1);
  chrome.alarms.create(ALARM_NAME, {
    periodInMinutes: intervalMinutes
  });
  
  // Do first check immediately
  checkAvailability();
}

// Tab-based monitoring (new method)
async function startTabMonitoring(config) {
  console.log('Starting tab-based monitoring');
  
  // Calculate timestamp for deep link
  const [day, month, year] = config.date.split('/');
  const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day), 0, 0, 0);
  const timestamp = date.getTime();
  
  // Build Vatican URL
  const url = `https://tickets.museivaticani.va/home/fromtag/${config.visitors}/${timestamp}/MV-Biglietti/1`;
  
  // Check if Vatican tab already exists
  const tabs = await chrome.tabs.query({ url: 'https://tickets.museivaticani.va/*' });
  
  let vaticanTab;
  if (tabs.length > 0) {
    // Reuse existing tab
    vaticanTab = tabs[0];
    await chrome.tabs.update(vaticanTab.id, { url, active: true });
  } else {
    // Create new tab
    vaticanTab = await chrome.tabs.create({ url, active: true });
  }
  
  // Store tab ID
  await chrome.storage.local.set({ vaticanTabId: vaticanTab.id });
  
  // Create alarm for periodic reloads
  chrome.alarms.create('tabReload', {
    periodInMinutes: config.checkInterval / 60
  });
  
  // Listen for tab reload alarm
  chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'tabReload') {
      await reloadVaticanTab();
    }
  });
}

// Stop monitoring
async function stopMonitoring() {
  console.log('Stopping monitoring');
  chrome.alarms.clear(ALARM_NAME);
  chrome.alarms.clear('tabReload');
  
  // Clear check in progress flag
  await chrome.storage.local.set({ checkInProgress: false });
  
  // Close Vatican tab if in tab mode
  const { vaticanTabId } = await chrome.storage.local.get('vaticanTabId');
  if (vaticanTabId) {
    try {
      await chrome.tabs.remove(vaticanTabId);
    } catch (error) {
      // Tab may already be closed
      console.log('Vatican tab already closed');
    }
    await chrome.storage.local.remove('vaticanTabId');
  }
  
  // Notify popup
  chrome.runtime.sendMessage({ action: 'monitoringStopped' });
}

// Reload Vatican tab and check for availability
async function reloadVaticanTab() {
  try {
    const { vaticanTabId, monitorConfig, checkInProgress } = await chrome.storage.local.get(['vaticanTabId', 'monitorConfig', 'checkInProgress']);
    
    if (!vaticanTabId || !monitorConfig?.isActive) {
      console.log('Tab monitoring not active');
      return;
    }
    
    // ✅ COOLDOWN: Don't reload if a check is already in progress
    if (checkInProgress) {
      console.log('⏳ Check already in progress, skipping reload...');
      return;
    }
    
    // Check if tab still exists
    try {
      const tab = await chrome.tabs.get(vaticanTabId);
      
      // Set check in progress flag
      await chrome.storage.local.set({ checkInProgress: true });
      console.log('🔄 Starting new check cycle...');
      
      // ✅ UPDATE MONITORING STATS
      chrome.runtime.sendMessage({ action: 'updateMonitoringStats' });
      
      // Reload the tab
      await chrome.tabs.reload(vaticanTabId);
      console.log('Vatican tab reloaded');
      
      // Wait for page to load, then check availability
      chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
        if (tabId === vaticanTabId && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          
          // Send message to content script to check availability
          chrome.tabs.sendMessage(vaticanTabId, {
            action: 'checkAvailabilityOnPage'
          }).catch(err => console.log('Content script not ready yet'));
        }
      });
      
      // ✅ SAFETY: Clear flag after 30 seconds (in case check gets stuck)
      setTimeout(async () => {
        await chrome.storage.local.set({ checkInProgress: false });
        console.log('✅ Check cycle timeout - ready for next check');
      }, 30000);
      
    } catch (error) {
      console.log('Vatican tab was closed, stopping monitoring');
      await chrome.storage.local.set({ checkInProgress: false });
      await stopMonitoring();
    }
    
  } catch (error) {
    console.error('Error reloading Vatican tab:', error);
    await chrome.storage.local.set({ checkInProgress: false });
  }
}

// Check availability
async function checkAvailability() {
  try {
    const { monitorConfig } = await chrome.storage.local.get('monitorConfig');
    
    if (!monitorConfig?.isActive) {
      console.log('Monitoring not active, skipping check');
      return;
    }
    
    console.log('Checking availability for:', monitorConfig.date);
    
    // Determine tag based on ticket type
    const tag = monitorConfig.ticketType === 0 ? 'MV-Biglietti' : 'MV-Visite-Guidate';
    
    // Step 1: Get fresh ticket IDs via Search API
    const searchUrl = new URL(`${VATICAN_BASE}/api/search/resultPerTag`);
    searchUrl.searchParams.set('lang', 'it');
    searchUrl.searchParams.set('visitorNum', monitorConfig.visitors);
    searchUrl.searchParams.set('visitDate', monitorConfig.date);
    searchUrl.searchParams.set('area', '1');
    searchUrl.searchParams.set('who', '');
    searchUrl.searchParams.set('page', '0');
    searchUrl.searchParams.set('tag', tag);
    
    const searchResponse = await fetch(searchUrl.toString(), {
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': `${VATICAN_BASE}/`
      }
    });
    
    if (!searchResponse.ok) {
      console.error('Search API failed:', searchResponse.status);
      return;
    }
    
    const searchData = await searchResponse.json();
    const visits = searchData.visits || [];
    
    // Find the right ticket
    const ticket = findTicket(visits, monitorConfig.ticketType);
    
    if (!ticket) {
      console.log('No matching ticket found');
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: false,
        message: 'No matching ticket found',
        timestamp: Date.now()
      });
      return;
    }
    
    console.log('Found ticket:', ticket.name, 'ID:', ticket.id);
    
    // ✅ OPTIMIZATION: Skip timeavail if search API already says SOLD_OUT or NOT_ALLOWED
    // Vatican returns HTTP 500 on timeavail for sold-out tickets - no point calling it
    if (ticket.availability === 'SOLD_OUT' || ticket.availability === 'NOT_ALLOWED') {
      console.log('⏭️ Search API says', ticket.availability, '- skipping timeavail');
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: false,
        message: `Ticket status: ${ticket.availability}`,
        timestamp: Date.now()
      });
      return;
    }
    
    // Step 2: Check time slots via timeavail API
    const timeavailUrl = new URL(`${VATICAN_BASE}/api/visit/timeavail`);
    timeavailUrl.searchParams.set('lang', 'it');
    timeavailUrl.searchParams.set('visitLang', monitorConfig.language || '');
    timeavailUrl.searchParams.set('visitTypeId', ticket.id);
    timeavailUrl.searchParams.set('visitorNum', monitorConfig.visitors);
    timeavailUrl.searchParams.set('visitDate', monitorConfig.date);
    
    const timeavailResponse = await fetch(timeavailUrl.toString(), {
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': `${VATICAN_BASE}/`
      }
    });
    
    // ✅ Handle HTTP 500 as "sold out" (Vatican returns 500 for sold-out tickets)
    if (timeavailResponse.status === 500) {
      console.log('⏭️ Timeavail returned 500 (sold out)');
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: false,
        message: 'No available time slots (500)',
        timestamp: Date.now()
      });
      return;
    }
    
    if (!timeavailResponse.ok) {
      console.error('Timeavail API failed:', timeavailResponse.status);
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: false,
        message: `API error: ${timeavailResponse.status}`,
        timestamp: Date.now()
      });
      return;
    }
    
    const timeavailData = await timeavailResponse.json();
    const timetable = timeavailData.timetable || [];
    
    // ✅ Filter available slots (must be AVAILABLE and have residual > 0 if present)
    const availableSlots = timetable.filter(slot => 
      slot.availability === 'AVAILABLE' &&
      (slot.residual === undefined || slot.residual === null || slot.residual > 0)
    );
    
    console.log(`Found ${availableSlots.length}/${timetable.length} available slots`);
    
    if (availableSlots.length > 0) {
      // Save available slots
      await saveAvailableSlots(availableSlots.map(slot => ({
        date: monitorConfig.date,
        time: slot.time,
        slotId: slot.id,
        visitors: monitorConfig.visitors,
        ticketId: ticket.id,
        ticketName: ticket.name
      })));
      
      // Send notification
      sendNotification(
        'Vatican Tickets Available! 🎉',
        `${availableSlots.length} slot(s) available for ${monitorConfig.date}`
      );
      
      // Add result
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: true,
        slotsCount: availableSlots.length,
        timestamp: Date.now()
      });
      
      // If auto-booking enabled, trigger it
      if (monitorConfig.autoBooking) {
        console.log('Auto-booking enabled - triggering booking flow');
        await triggerAutoBooking(monitorConfig, availableSlots[0]);
      }
    } else {
      addResult({
        date: monitorConfig.date,
        visitors: monitorConfig.visitors,
        available: false,
        message: 'No available time slots',
        timestamp: Date.now()
      });
    }
    
  } catch (error) {
    console.error('Error checking availability:', error);
  }
}

// Find ticket based on type
function findTicket(visits, ticketType) {
  const EXCLUDED = ['pellegrinaggi', 'lunch', 'pranzo', 'gruppi', 'specola', 'palazzo', 'didattiche'];
  
  // For standard tickets (type 0)
  if (ticketType === 0) {
    // ✅ FIX: Don't require AVAILABLE at search level - check timeavail instead
    // Only skip if explicitly SOLD_OUT or NOT_ALLOWED
    return visits.find(v => 
      v.name.toLowerCase().includes('musei vaticani') &&
      v.name.toLowerCase().includes('ingresso') &&
      !EXCLUDED.some(ex => v.name.toLowerCase().includes(ex)) &&
      v.availability !== 'SOLD_OUT' &&
      v.availability !== 'NOT_ALLOWED'
    );
  }
  
  // For guided tours (type 1)
  return visits.find(v =>
    v.name.toLowerCase().includes('musei vaticani') &&
    v.name.toLowerCase().includes('guidat') &&
    !EXCLUDED.some(ex => v.name.toLowerCase().includes(ex)) &&
    v.availability !== 'SOLD_OUT' &&
    v.availability !== 'NOT_ALLOWED'
  );
}

// Add result to history
async function addResult(result) {
  const { results = [] } = await chrome.storage.local.get('results');
  results.push(result);
  
  // Keep only last 50 results
  const trimmedResults = results.slice(-50);
  
  await chrome.storage.local.set({ results: trimmedResults });
  
  // Notify popup
  chrome.runtime.sendMessage({ 
    action: 'updateResults', 
    results: trimmedResults 
  });
}

// Save available slots
async function saveAvailableSlots(newSlots) {
  const { availableSlots = [] } = await chrome.storage.local.get('availableSlots');
  
  // Add new slots (avoid duplicates)
  const updatedSlots = [...availableSlots];
  
  for (const slot of newSlots) {
    const exists = updatedSlots.some(s => 
      s.date === slot.date && 
      s.time === slot.time && 
      s.visitors === slot.visitors
    );
    
    if (!exists) {
      updatedSlots.push(slot);
    }
  }
  
  // Keep only last 20 slots
  const trimmedSlots = updatedSlots.slice(-20);
  
  await chrome.storage.local.set({ availableSlots: trimmedSlots });
  
  // Notify popup
  chrome.runtime.sendMessage({ 
    action: 'updateSlots', 
    slots: trimmedSlots 
  });
}

// Send browser notification
function sendNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: title,
    message: message,
    priority: 2
  });
  
  // Play sound (optional)
  // You can add an audio file and play it here
}

// Trigger auto-booking flow
async function triggerAutoBooking(config, firstSlot) {
  try {
    console.log('Starting auto-booking flow...');
    
    // Stop monitoring
    await stopMonitoring();
    
    // Open Vatican website in new tab
    const tab = await chrome.tabs.create({
      url: 'https://tickets.museivaticani.va/home',
      active: true
    });
    
    // Wait for tab to load
    await new Promise(resolve => {
      chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
        if (tabId === tab.id && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      });
    });
    
    // Wait a bit more for page to fully load
    await sleep(2000);
    
    // Send message to content script to start auto-booking
    chrome.tabs.sendMessage(tab.id, {
      action: 'startAutoBooking',
      config: {
        date: config.date,
        visitors: config.visitors,
        ticketType: config.ticketType,
        language: config.language,
        preferredTime: firstSlot.time,
        profile: config.profile,
        autoConfirm: config.profile?.autoConfirm || false
      }
    });
    
    console.log('Auto-booking flow initiated');
    
  } catch (error) {
    console.error('Error triggering auto-booking:', error);
    sendNotification('Auto-booking Error', error.message);
  }
}

// Listen for auto-booking progress updates
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'autoBookingProgress') {
    console.log(`[Auto-booking] ${message.message}`);
    
    // Show notification for important steps
    if (message.type === 'success' || message.type === 'error') {
      sendNotification('Auto-booking Update', message.message);
    }
  } else if (message.action === 'ticketsFoundOnPage') {
    console.log(`Tickets found on page: ${message.count}`);
    
    // ✅ Clear check in progress flag
    chrome.storage.local.set({ checkInProgress: false });
    console.log('✅ Check complete - tickets found!');
    
    // Get monitoring config to show proper date/visitors
    chrome.storage.local.get('monitorConfig', (data) => {
      const config = data.monitorConfig || {};
      
      // Send desktop notification
      sendNotification(
        'Vatican Tickets Available! 🎉',
        `${message.count} slot(s) available for ${config.date || 'selected date'}`
      );
      
      // Add result with proper config
      addResult({
        date: config.date || 'Unknown',
        visitors: config.visitors || 'N/A',
        available: true,
        slotsCount: message.count,
        timestamp: Date.now(),
        source: 'tab_reload',
        slots: message.slots || []
      });
    });
  } else if (message.action === 'noTicketsOnPage') {
    console.log('No tickets found on page');
    
    // ✅ Clear check in progress flag
    chrome.storage.local.set({ checkInProgress: false });
    console.log('✅ Check complete - no tickets');
    
    // Get monitoring config to show proper date/visitors
    chrome.storage.local.get('monitorConfig', (data) => {
      const config = data.monitorConfig || {};
      
      // Add result with proper config
      addResult({
        date: config.date || 'Unknown',
        visitors: config.visitors || 'N/A',
        available: false,
        message: 'No time slots available',
        timestamp: Date.now(),
        source: 'tab_reload'
      });
    });
  } else if (message.action === 'rateLimited') {
    console.error('⚠️ RATE LIMITED - Stopping monitoring');
    
    // Clear check in progress flag
    chrome.storage.local.set({ checkInProgress: false });
    
    // Send notification
    sendNotification(
      '⚠️ Rate Limited!',
      'Vatican is blocking requests. Increase check interval to 30-60 seconds and try again later.'
    );
    
    // Add result
    chrome.storage.local.get('monitorConfig', (data) => {
      const config = data.monitorConfig || {};
      addResult({
        date: config.date || 'Unknown',
        visitors: config.visitors || 'N/A',
        available: false,
        message: '⚠️ Rate limited - increase interval',
        timestamp: Date.now(),
        source: 'tab_reload'
      });
    });
    
    // Optionally stop monitoring
    // await stopMonitoring();
  }
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// BACKEND LISTENER MODE - Listen to backend and auto-book in incognito windows
// ============================================================================

let backendPollingInterval = null;
let activeBookingWindows = new Map(); // Track active booking windows
let processedSlotIds = new Set(); // Track slots we've already opened windows for

/**
 * Start backend listener mode
 * Polls backend API for available slots and opens incognito windows to book
 */
async function startBackendListener(config) {
  console.log('🚀 Starting Backend Listener Mode');
  console.log('Config:', config);
  
  // Save config
  await chrome.storage.local.set({ 
    backendListenerConfig: config,
    backendListenerActive: true
  });
  
  // Clear any existing interval
  if (backendPollingInterval) {
    clearInterval(backendPollingInterval);
  }
  
  // Poll backend every 10 seconds for available slots
  backendPollingInterval = setInterval(async () => {
    await checkBackendForAvailableSlots(config);
  }, 10000);
  
  // Check immediately
  await checkBackendForAvailableSlots(config);
  
  console.log('✅ Backend listener started - polling every 10 seconds');
}

/**
 * Stop backend listener mode
 */
async function stopBackendListener() {
  console.log('🛑 Stopping Backend Listener Mode');
  
  // Clear polling interval
  if (backendPollingInterval) {
    clearInterval(backendPollingInterval);
    backendPollingInterval = null;
  }
  
  // Close all active booking windows
  for (const [windowId, slotInfo] of activeBookingWindows.entries()) {
    try {
      await chrome.windows.remove(windowId);
      console.log(`Closed booking window for ${slotInfo.date}`);
    } catch (error) {
      console.log(`Window ${windowId} already closed`);
    }
  }
  
  activeBookingWindows.clear();
  processedSlotIds.clear(); // Clear processed slots tracking
  
  // Update storage
  await chrome.storage.local.set({ 
    backendListenerActive: false 
  });
  
  console.log('✅ Backend listener stopped');
}

/**
 * Check backend API for available slots
 */
async function checkBackendForAvailableSlots(config) {
  try {
    const backendUrl = config.backendUrl || 'http://localhost:8000';
    const apiKey = config.apiKey || '';
    
    // ✅ UPDATE MONITORING STATS
    chrome.runtime.sendMessage({ action: 'updateMonitoringStats' });
    
    // Call backend API to get available slots
    const response = await fetch(`${backendUrl}/api/v1/available-slots/`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.error('Backend API error:', response.status);
      return;
    }
    
    const data = await response.json();
    
    if (data.slots && data.slots.length > 0) {
      console.log(`🎉 Found ${data.slots.length} available slots from backend!`);
      
      // Filter out slots we've already processed
      const newSlots = data.slots.filter(slot => !processedSlotIds.has(slot.id));
      
      if (newSlots.length === 0) {
        console.log('All slots already processed, waiting for new slots...');
        return;
      }
      
      console.log(`📋 ${newSlots.length} new slots to process (${data.slots.length - newSlots.length} already opened)`);
      
      // Open incognito windows for each NEW slot (max 10 at a time)
      const maxWindows = config.maxConcurrentBookings || 10;
      const slotsToBook = newSlots.slice(0, maxWindows);
      
      // Mark these slots as processed
      slotsToBook.forEach(slot => processedSlotIds.add(slot.id));
      
      await openIncognitoBookingWindows(slotsToBook, config);
      
      // Send notification
      sendNotification(
        `${slotsToBook.length} Tickets Ready to Book!`,
        `Opening ${slotsToBook.length} incognito windows for parallel booking`
      );
    } else {
      console.log('No available slots yet, continuing to poll...');
    }
    
  } catch (error) {
    console.error('Error checking backend for slots:', error);
  }
}

/**
 * Open incognito windows for multiple slots
 * Each window books a different date in parallel
 */
async function openIncognitoBookingWindows(slots, config) {
  console.log(`📦 Opening ${slots.length} incognito windows for parallel booking`);
  
  for (let i = 0; i < slots.length; i++) {
    const slot = slots[i];
    
    try {
      // Build Vatican URL for this slot
      const vaticanUrl = buildVaticanBookingUrl(slot);
      
      // Determine mode: hold or auto-book
      const useHoldMode = config.holdMode || false;
      
      // Open NEW INCOGNITO WINDOW (isolated session - no conflicts!)
      const window = await chrome.windows.create({
        url: vaticanUrl,
        incognito: true,  // ✅ Isolated session
        focused: i === 0, // Focus first window only
        type: 'normal'
        // Note: 'state' parameter removed - causes "Invalid value for state" error in some Chrome versions
      });
      
      // Track this booking window
      activeBookingWindows.set(window.id, {
        slotId: slot.id,
        date: slot.date,
        time: slot.time,
        ticketId: slot.ticketId,
        visitors: slot.visitors,
        startedAt: Date.now(),
        mode: useHoldMode ? 'hold' : 'auto'
      });
      
      console.log(`✅ Opened incognito window #${i + 1} for ${slot.date} ${slot.time} (${useHoldMode ? 'HOLD' : 'AUTO'} mode)`);
      
      // Wait for page to load, then inject script with retry logic
      const sendMessageWithRetry = async (tabId, message, maxRetries = 5) => {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
          try {
            await chrome.tabs.sendMessage(tabId, message);
            console.log(`✅ Message sent to tab ${tabId} (attempt ${attempt})`);
            return true;
          } catch (err) {
            if (attempt < maxRetries) {
              console.log(`⏳ Content script not ready yet (attempt ${attempt}/${maxRetries}), retrying in 2s...`);
              await sleep(2000);
            } else {
              console.error(`❌ Failed to send message after ${maxRetries} attempts:`, err.message);
              return false;
            }
          }
        }
      };
      
      setTimeout(async () => {
        const tabs = await chrome.tabs.query({ windowId: window.id });
        if (tabs.length > 0) {
          const message = useHoldMode ? {
            action: 'startHoldMode',
            slot: slot,
            config: {
              date: slot.date,
              time: slot.time,
              visitors: slot.visitors,
              ticketId: slot.ticket_id,
              ticketType: slot.language ? 1 : 0,
              language: slot.language,
              profile: slot.profile,
              participants: slot.participants,
              card: slot.card,
              holdMode: true
            }
          } : {
            action: 'startAutoBooking',
            slot: {
              id: slot.id,
              date: slot.date,
              time: slot.time,
              ticket_id: slot.ticket_id,
              ticket_name: slot.ticket_name,
              visitors: slot.visitors,
              adult_count: slot.adult_count,
              child_count: slot.child_count,
              language: slot.language,
              profile: slot.profile,
              participants: slot.participants
            },
            config: {
              date: slot.date,
              time: slot.time,
              preferredTime: slot.time,  // Add this for content script compatibility
              visitors: slot.visitors,
              ticketId: slot.ticket_id,
              ticketType: slot.language ? 1 : 0,
              language: slot.language,
              profile: slot.profile,
              participants: slot.participants,
              card: slot.card,
              autoConfirm: true,
              autoPay: config.autoPay !== false
            }
          };
          
          await sendMessageWithRetry(tabs[0].id, message);
        }
      }, 3000);  // Wait 3 seconds for page to load initially
      
      // Small delay between opening windows to avoid overwhelming
      await sleep(500);
      
    } catch (error) {
      console.error(`Error opening incognito window for ${slot.date}:`, error);
    }
  }
  
  console.log(`✅ Opened ${slots.length} incognito windows successfully`);
}

/**
 * Build Vatican booking URL for a specific slot
 * Opens the deep link directly to the ticket selection page
 */
function buildVaticanBookingUrl(slot) {
  const baseUrl = 'https://tickets.museivaticani.va';
  
  console.log(`Building Vatican URL for slot:`);
  console.log(`  Date: ${slot.date} ${slot.time}`);
  console.log(`  Ticket: ${slot.ticket_name} (ID: ${slot.ticket_id})`);
  console.log(`  Visitors: ${slot.visitors}`);
  
  // Parse date from DD/MM/YYYY format
  const [day, month, year] = slot.date.split('/');
  const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day), 0, 0, 0);
  
  // Calculate timestamp in milliseconds
  const timestamp = date.getTime();
  
  // Determine ticket category (standard vs guided tour)
  const category = slot.language ? 'MV-Visite-Guidate' : 'MV-Biglietti';
  
  // Build deep link URL
  const url = `${baseUrl}/home/fromtag/${slot.visitors}/${timestamp}/${category}/1`;
  
  console.log(`  Deep link: ${url}`);
  
  return url;
}

/**
 * Listen for window close events to track completed bookings
 */
chrome.windows.onRemoved.addListener(async (windowId) => {
  if (activeBookingWindows.has(windowId)) {
    const slotInfo = activeBookingWindows.get(windowId);
    const duration = Math.round((Date.now() - slotInfo.startedAt) / 1000);
    
    console.log(`Booking window closed for ${slotInfo.date} (duration: ${duration}s)`);
    
    activeBookingWindows.delete(windowId);
    
    // Check if all windows are closed
    if (activeBookingWindows.size === 0) {
      console.log('✅ All booking windows closed - checking for more tasks');
      
      // Check backend again for more available slots
      const { backendListenerConfig, backendListenerActive } = await chrome.storage.local.get([
        'backendListenerConfig',
        'backendListenerActive'
      ]);
      
      if (backendListenerActive && backendListenerConfig) {
        console.log('🔄 Checking backend for more available slots...');
        await checkBackendForAvailableSlots(backendListenerConfig);
      }
    }
  }
});

/**
 * Listen for booking completion messages from content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'bookingCompleted') {
    console.log(`✅ Booking completed for ${message.date}`);
    
    // Mark slot as booked in backend
    markSlotAsBooked(message.slotId);
    
    // Close the booking window
    if (sender.tab && sender.tab.windowId) {
      chrome.windows.remove(sender.tab.windowId);
    }
    
  } else if (message.action === 'bookingFailed') {
    console.error(`❌ Booking failed for ${message.date}: ${message.error}`);
    
    // Optionally retry or notify user
    sendNotification(
      'Booking Failed',
      `Failed to book ${message.date}: ${message.error}`
    );
    
  } else if (message.action === 'bookingPaused') {
    console.log(`⏸️ Booking paused for ${message.date} ${message.time}: ${message.message}`);
    
    // Send notification
    sendNotification(
      'Form Ready for Review',
      `${message.date} ${message.time} - Form filled, please review and click ACQUISTA manually`
    );
    
  } else if (message.action === 'paymentLinkReady') {
    console.log('💳 Payment link ready:', message.url);
    
    // Send notification with payment link
    sendNotification(
      'Payment Link Ready',
      `Payment page loaded: ${message.url}`
    );
  }
});

/**
 * Mark slot as booked in backend
 */
async function markSlotAsBooked(slotId) {
  try {
    const { backendListenerConfig } = await chrome.storage.local.get('backendListenerConfig');
    
    if (!backendListenerConfig) return;
    
    const backendUrl = backendListenerConfig.backendUrl || 'http://localhost:8000';
    const apiKey = backendListenerConfig.apiKey || '';
    
    await fetch(`${backendUrl}/api/slots/${slotId}/mark-booked`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`Marked slot ${slotId} as booked in backend`);
    
  } catch (error) {
    console.error('Error marking slot as booked:', error);
  }
}
