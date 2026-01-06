# Admin Dashboard - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend
```bash
cd backend
python main.py
```

Backend runs on: **http://localhost:8001**

### Step 2: Login as Admin
```bash
curl -X POST http://localhost:8001/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Save the `access_token` from the response.

### Step 3: Access Admin Dashboard
Open: **http://localhost:8001/docs**
- Click "Authorize" button
- Enter: `Bearer <your_access_token>`
- Explore all admin endpoints under "Admin" tag

---

## 📊 Key Endpoints

### Dashboard Overview
```bash
GET /api/admin/dashboard/overview
```
Returns: Orders, revenue, drivers, performance stats

### Live Map
```bash
GET /api/admin/live-map
```
Returns: Real-time driver and order locations

### List Orders
```bash
GET /api/admin/orders?status=in_transit&city=Casablanca
```
Returns: Filtered order list

### Reassign Order
```bash
POST /api/admin/orders/{order_id}/reassign
Body: {"new_driver_id": "DRV002", "reason": "Driver change"}
```

### Suspend Driver
```bash
POST /api/admin/drivers/{driver_id}/suspend
Body: {"suspend": true, "reason": "Customer complaints"}
```

---

## 🎯 What You Can Do

✅ **Monitor System**
- View real-time statistics
- Track all drivers on map
- See active deliveries
- Monitor performance metrics

✅ **Manage Orders**
- Search and filter orders
- View order details
- Reassign to different drivers
- Cancel orders

✅ **Manage Drivers**
- View all drivers by city
- Check driver performance
- Suspend/activate drivers
- View earnings and stats

✅ **Analyze Data**
- Revenue by period
- Performance by city
- Driver utilization
- Success rates

✅ **Handle Alerts**
- Delayed orders
- Low driver availability
- System issues

---

## 🔑 Admin Credentials

**Username**: `admin`  
**Password**: `admin123`

---

## 📱 Test with cURL

### Get Dashboard
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/admin/dashboard/overview
```

### Get Active Orders
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8001/api/admin/orders?status=in_transit"
```

### Get Revenue Analytics
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8001/api/admin/analytics/revenue?period=week"
```

---

## 🎨 Frontend Integration

Use these APIs to build your admin dashboard:

```javascript
// Example: Get dashboard data
const token = localStorage.getItem('admin_token');

const getDashboard = async () => {
  const res = await fetch('/api/admin/dashboard/overview', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await res.json();
};

// Example: Reassign order
const reassignOrder = async (orderId, newDriverId) => {
  const res = await fetch(`/api/admin/orders/${orderId}/reassign`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      new_driver_id: newDriverId,
      reason: 'Manual reassignment'
    })
  });
  return await res.json();
};
```

---

## 📚 Full Documentation

- **API Docs**: `ADMIN_API_DOCS.md`
- **Implementation**: `ADMIN_IMPLEMENTATION.md`
- **Swagger UI**: http://localhost:8001/docs

---

## ✅ Status

**Backend**: ✅ Complete and ready  
**Frontend**: 🔨 Ready to build  
**Testing**: ✅ All endpoints working

---

## 🎯 Next Steps

1. ✅ Backend admin API is complete
2. 🔨 Build React admin dashboard UI
3. 🔨 Add real-time updates with WebSockets
4. 🔨 Create charts and visualizations
5. 🔨 Add export functionality

**The admin backend is ready for frontend development!** 🚀
