# Testing Checklist

## 🔴 CRITICAL - Must Test Before Production

### Authentication
- [ ] Customer login persists after page reload
- [ ] Driver login persists after page reload
- [ ] Admin login persists after page reload
- [ ] Logout clears auth and redirects correctly
- [ ] Invalid credentials show error message
- [ ] Token expiry (24h) works - force test by setting past expiry

### Order Creation
- [ ] Create local order (same city)
- [ ] Create inter-city order
- [ ] Order appears in dashboard after creation
- [ ] Pricing calculation is correct
- [ ] All form fields validate properly

### Driver Assignment
- [ ] Order gets assigned to correct city driver
- [ ] 16 drivers are available in system
- [ ] Assignment algorithm picks best driver
- [ ] Driver receives order in their dashboard
- [ ] Multiple orders to same driver work

### Order Tracking
- [ ] Track by tracking number works
- [ ] Real-time location updates (if GPS enabled)
- [ ] Status changes reflect correctly
- [ ] Order history shows all events

### Driver Dashboard
- [ ] Driver sees assigned orders
- [ ] Can accept/reject assignments
- [ ] Can start delivery
- [ ] Can complete delivery
- [ ] GPS tracking updates location
- [ ] Multi-package route optimization works

## ⚠️ IMPORTANT - Should Test

### API Endpoints
- [ ] GET /api/orders returns data
- [ ] POST /api/orders creates order
- [ ] GET /api/drivers/by-city shows all 16 drivers
- [ ] GET /api/system/coverage shows city stats
- [ ] GET /api/assignment/simulate works
- [ ] WebSocket connections (if implemented)

### UI/UX
- [ ] All pages load without errors
- [ ] Mobile responsive design works
- [ ] Navigation between pages smooth
- [ ] Forms submit correctly
- [ ] Error messages display properly
- [ ] Loading states show correctly

### Data Persistence
- [ ] Orders persist in memory (until server restart)
- [ ] Driver status updates persist
- [ ] Order status changes persist
- [ ] GPS location history saves

## 💡 NICE TO HAVE - Optional Tests

### Performance
- [ ] Page load times < 2 seconds
- [ ] API response times < 500ms
- [ ] No memory leaks in browser
- [ ] GPS updates don't lag

### Edge Cases
- [ ] What happens with 0 available drivers?
- [ ] What if order city has no drivers?
- [ ] What if GPS permission denied?
- [ ] What if backend is down?
- [ ] What if invalid tracking number?

### Browser Compatibility
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

## 🚫 KNOWN ISSUES (Don't Test Yet)

### Not Implemented
- [ ] MongoDB integration (using in-memory data)
- [ ] CrewAI agents (not connected)
- [ ] Real JWT validation (hardcoded tokens)
- [ ] Password hashing (plain text)
- [ ] Email/SMS notifications
- [ ] Real routing APIs (Google Maps/OpenRouteService)
- [ ] Payment processing
- [ ] Warehouse management workflow
- [ ] Real-time WebSocket updates

### Will Break
- [ ] Server restart loses all data
- [ ] Token validation is fake
- [ ] Inter-city warehouse flow incomplete
- [ ] GPS geofencing not implemented
- [ ] Notification system not connected

## 🧪 Quick Test Script

### 1. Test Customer Flow (5 min)
```
1. Go to http://localhost:5173
2. Click "Login"
3. Enter: testuser / test123
4. Should redirect to dashboard
5. Refresh page - should stay logged in
6. Click "New Order"
7. Fill form and submit
8. Check order appears in dashboard
9. Click tracking number
10. Verify order details shown
```

### 2. Test Driver Flow (5 min)
```
1. Open new incognito window
2. Go to http://localhost:5173/driver/login
3. Enter: ahmed@delivery.ma / driver123
4. Should redirect to driver dashboard
5. Refresh page - should stay logged in
6. Check if orders appear
7. Try accepting an order
8. Try starting delivery
9. Try completing delivery
```

### 3. Test Assignment (3 min)
```
1. Go to http://localhost:8001/api/system/coverage
2. Verify 16 drivers shown
3. Go to http://localhost:8001/api/assignment/simulate?pickup_city=Casablanca
4. Verify driver scoring works
5. Check best match is selected
```

### 4. Test API (2 min)
```
1. Open http://localhost:8001/docs
2. Try GET /api/orders
3. Try GET /api/drivers/by-city
4. Try POST /api/orders (use example)
5. Verify responses are correct
```

## ✅ Success Criteria

**Minimum to call it "working":**
- ✅ Login persists after reload
- ✅ Can create orders
- ✅ Orders get assigned to drivers
- ✅ Driver can see and manage orders
- ✅ Tracking shows order status
- ✅ 16 drivers available across 6 cities

**Ready for demo:**
- All above +
- ✅ Clean UI with no visual bugs
- ✅ No console errors
- ✅ Mobile responsive
- ✅ All test credentials work

**Production ready:**
- All above +
- ✅ MongoDB connected
- ✅ Real authentication
- ✅ CrewAI agents integrated
- ✅ Error handling everywhere
- ✅ Input validation
- ✅ Security measures

## 🎯 Priority Order

1. **Test auth persistence** (most important fix)
2. **Test order creation flow** (core feature)
3. **Test driver assignment** (core feature)
4. **Test driver dashboard** (core feature)
5. **Test tracking** (user-facing)
6. **Test API endpoints** (backend validation)
7. **Test UI/UX** (polish)
8. **Test edge cases** (robustness)
