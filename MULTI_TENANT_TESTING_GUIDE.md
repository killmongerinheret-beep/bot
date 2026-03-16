# Multi-Tenant Testing Guide ✅

**Status**: Demo data created successfully  
**Agencies**: 3 agencies with separate users and tasks  
**Purpose**: Verify complete data isolation between agencies

---

## 🏢 TEST AGENCIES & CREDENTIALS

### Agency 1: Alpha Travel Agency
```
Username: alpha_travel
Password: alpha123
Plan: Free
Tasks: 4 monitors
```

### Agency 2: Beta Tours & Travel  
```
Username: beta_tours
Password: beta123
Plan: Standard
Tasks: 2 monitors
```

### Agency 3: Gamma Vacation Services
```
Username: gamma_vacation
Password: gamma123
Plan: Premium
Tasks: 1 monitor
```

---

## 📋 EXPECTED TASK DISTRIBUTION

### Alpha Travel Agency (4 tasks)
- ✅ Standard Entry - 2 dates (10/03/2026, 11/03/2026)
- ✅ Standard Entry - 1 date (23/03/2026)
- ✅ Guided Tour (English) - 1 date
- ✅ Guided Tour (Italian) - 2 dates

### Beta Tours & Travel (2 tasks)
- ✅ Standard Entry - 2 dates (future dates)
- ✅ Guided Tour (Italian) - 1 date

### Gamma Vacation Services (1 task)
- ✅ Guided Tour (French) - 2 dates (future dates)

---

## 🧪 TESTING PROCEDURE

### Step 1: Test Alpha Travel Agency
1. Go to: https://bot-front-beta.vercel.app
2. Login with: `alpha_travel` / `alpha123`
3. **Expected Result**: See 4 tasks only
4. **Verify**: All tasks belong to Alpha Travel Agency
5. **Test**: Try to create a new monitor
6. **Test**: Try to delete a monitor
7. Logout

### Step 2: Test Beta Tours & Travel
1. Login with: `beta_tours` / `beta123`
2. **Expected Result**: See 2 different tasks
3. **Verify**: No Alpha Travel tasks visible
4. **Verify**: All tasks belong to Beta Tours
5. **Test**: Create/delete monitors
6. Logout

### Step 3: Test Gamma Vacation Services
1. Login with: `gamma_vacation` / `gamma123`
2. **Expected Result**: See 1 task only
3. **Verify**: No other agencies' tasks visible
4. **Verify**: Task is French guided tour
5. **Test**: Create/delete monitors
6. Logout

---

## ✅ ISOLATION VERIFICATION CHECKLIST

### Data Isolation
- [ ] Each user sees only their agency's tasks
- [ ] Task counts match expected numbers
- [ ] No cross-agency data leakage
- [ ] API responses filtered by agency

### Functional Isolation
- [ ] Can create monitors (adds to own agency only)
- [ ] Can delete monitors (own agency only)
- [ ] Cannot access other agencies' data
- [ ] Session management works per user

### UI Isolation
- [ ] Dashboard shows correct agency name
- [ ] Stats reflect only own agency data
- [ ] No agency selector visible (single agency per user)
- [ ] Logout works correctly

---

## 🔍 TECHNICAL VERIFICATION

### API Endpoint Tests

**Test 1: Tasks API**
```bash
# Login as alpha_travel, then check tasks
curl -H "Authorization: Bearer <token>" \
  https://southwest-happens-rail-creativity.trycloudflare.com/api/v1/tasks/
# Should return 4 tasks for Alpha Travel only
```

**Test 2: Cross-Agency Access**
```bash
# Try to access specific task ID from different agency
# Should return 404 or permission denied
```

### Database Verification
```sql
-- Check task distribution
SELECT agency.name, COUNT(tasks.id) as task_count 
FROM monitors_agency agency 
LEFT JOIN monitors_monitortask tasks ON agency.id = tasks.agency_id 
GROUP BY agency.name;

-- Expected results:
-- Alpha Travel Agency: 4
-- Beta Tours & Travel: 2  
-- Gamma Vacation Services: 1
```

---

## 🚨 SECURITY TESTS

### Authentication Tests
- [ ] Cannot access dashboard without login
- [ ] Invalid credentials rejected
- [ ] Session expires appropriately
- [ ] Logout clears session

### Authorization Tests  
- [ ] Cannot view other agencies' tasks via API
- [ ] Cannot modify other agencies' data
- [ ] Cannot access admin functions (if not admin)
- [ ] API returns 403 for unauthorized access

### Session Tests
- [ ] Session tokens are unique per user
- [ ] Sessions don't leak between users
- [ ] Concurrent logins work correctly
- [ ] Session hijacking prevented

---

## 📊 EXPECTED DASHBOARD VIEWS

### Alpha Travel Dashboard
```
📊 Stats: Active: 4, Total: 4, Plan: Free
📋 Tasks:
  • Standard Entry (2 visitors) - 10/03/2026, 11/03/2026
  • Standard Entry (1 visitor) - 23/03/2026  
  • Guided Tour - English (4 visitors) - [future date]
  • Guided Tour - Italian (2 visitors) - [future dates]
```

### Beta Tours Dashboard
```
📊 Stats: Active: 2, Total: 2, Plan: Standard
📋 Tasks:
  • Standard Entry (1 visitor) - [future dates]
  • Guided Tour - Italian (3 visitors) - [future date]
```

### Gamma Vacation Dashboard
```
📊 Stats: Active: 1, Total: 1, Plan: Premium
📋 Tasks:
  • Guided Tour - French (2 visitors) - [future dates]
```

---

## 🐛 TROUBLESHOOTING

### Issue: Wrong number of tasks
**Check**: Database query filtering by agency
**Fix**: Verify API viewsets use `request.user.agency`

### Issue: Can see other agencies' data
**Check**: Authentication middleware
**Fix**: Ensure all API calls include agency filter

### Issue: Cannot create tasks
**Check**: User permissions and agency assignment
**Fix**: Verify user.agency is set correctly

### Issue: Login fails
**Check**: Password hash format and user creation
**Fix**: Re-run user creation script

---

## 📝 TEST REPORT TEMPLATE

```
MULTI-TENANT ISOLATION TEST REPORT
Date: [DATE]
Tester: [NAME]

ALPHA TRAVEL AGENCY:
✅/❌ Login successful
✅/❌ Sees 4 tasks only
✅/❌ Can create monitor
✅/❌ Can delete monitor
✅/❌ No other agency data visible

BETA TOURS & TRAVEL:
✅/❌ Login successful  
✅/❌ Sees 2 tasks only
✅/❌ Can create monitor
✅/❌ Can delete monitor
✅/❌ No other agency data visible

GAMMA VACATION SERVICES:
✅/❌ Login successful
✅/❌ Sees 1 task only
✅/❌ Can create monitor
✅/❌ Can delete monitor
✅/❌ No other agency data visible

SECURITY TESTS:
✅/❌ Cannot access without login
✅/❌ Sessions isolated per user
✅/❌ API enforces agency filtering
✅/❌ No cross-agency data leakage

OVERALL RESULT: ✅ PASS / ❌ FAIL
```

---

## 🎯 SUCCESS CRITERIA

Multi-tenant isolation is successful when:

1. **Complete Data Separation**: Each agency sees only their own data
2. **Functional Isolation**: Each agency can only modify their own data  
3. **Security Enforcement**: No way to access other agencies' data
4. **UI Consistency**: Dashboard reflects single agency context
5. **API Security**: All endpoints respect agency boundaries

---

**Ready for Testing**: ✅ YES  
**Test URL**: https://bot-front-beta.vercel.app  
**Expected Result**: Perfect multi-tenant isolation ✅

---

**Date**: March 12, 2026, 04:15 CET  
**Status**: DEMO DATA READY - START TESTING ✅