// Simple GPS and Routing Service
class GPSService {
  constructor() {
    this.watchId = null;
    this.currentPosition = null;
    this.isTracking = false;
    this.callbacks = [];
  }

  startTracking(callback) {
    if (!navigator.geolocation) {
      throw new Error('Geolocation not supported');
    }

    this.callbacks.push(callback);
    this.isTracking = true;

    this.watchId = navigator.geolocation.watchPosition(
      (position) => {
        this.currentPosition = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy || 10,
          speed: position.coords.speed || 0,
          timestamp: new Date().toISOString()
        };
        this.callbacks.forEach(cb => cb(this.currentPosition));
      },
      (error) => {
        console.error('GPS Error:', error);
        // Use fallback location (Casablanca)
        const fallback = {
          lat: 33.5731,
          lng: -7.5898,
          accuracy: 1000,
          speed: 0,
          timestamp: new Date().toISOString()
        };
        this.callbacks.forEach(cb => cb(fallback));
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 30000
      }
    );
  }

  stopTracking() {
    if (this.watchId) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
    this.isTracking = false;
    this.callbacks = [];
  }

  getCurrentPosition() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve({ lat: 33.5731, lng: -7.5898, accuracy: 1000, speed: 0 });
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy || 10,
            speed: position.coords.speed || 0
          });
        },
        () => {
          resolve({ lat: 33.5731, lng: -7.5898, accuracy: 1000, speed: 0 });
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    });
  }

  calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

  isWithinGeofence(targetLat, targetLng, radiusMeters = 100) {
    if (!this.currentPosition) return false;
    const distance = this.calculateDistance(
      this.currentPosition.lat, this.currentPosition.lng,
      targetLat, targetLng
    ) * 1000;
    return distance <= radiusMeters;
  }
}

export default new GPSService();