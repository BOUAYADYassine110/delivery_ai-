# Mobile Access Setup

## Quick Setup (Same WiFi)

1. **Find your computer's IP**:
   ```bash
   # Windows
   ipconfig
   
   # Mac/Linux  
   ifconfig
   ```

2. **Start the servers**:
   ```bash
   # Backend
   cd backend
   python main.py
   
   # Frontend
   cd frontend
   npm run dev -- --host 0.0.0.0
   ```

3. **Access from phone**:
   - Replace `localhost` with your IP address
   - Driver App: `http://YOUR_IP:5173/driver/login`
   - Admin Panel: `http://YOUR_IP:5173/admin/login`
   - Customer Portal: `http://YOUR_IP:5173/login`

## Example URLs
If your IP is `192.168.1.100`:
- Driver: `http://192.168.1.100:5173/driver/login`
- Admin: `http://192.168.1.100:5173/admin/login`
- API: `http://192.168.1.100:8000`

## Test Credentials
- **Driver**: driver@example.com / driver123
- **Admin**: admin / admin123
- **Customer**: testuser / test123

## Mobile Features
- ✅ GPS tracking
- ✅ Touch-optimized interface
- ✅ Real-time notifications
- ✅ Route optimization
- ✅ Order management
- ✅ Call integration
- ✅ Map navigation

## Troubleshooting
1. **Can't connect**: Check firewall settings
2. **Slow loading**: Ensure good WiFi signal
3. **GPS not working**: Allow location permissions
4. **API errors**: Verify backend is running on 0.0.0.0:8000