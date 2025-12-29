class GoogleMapsService {
  constructor() {
    this.directionsService = null;
    this.geocoder = null;
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;
    
    await this.waitForGoogleMaps();
    this.directionsService = new window.google.maps.DirectionsService();
    this.geocoder = new window.google.maps.Geocoder();
    this.initialized = true;
  }

  waitForGoogleMaps() {
    return new Promise((resolve) => {
      if (window.google && window.google.maps) {
        resolve();
      } else {
        const checkGoogle = setInterval(() => {
          if (window.google && window.google.maps) {
            clearInterval(checkGoogle);
            resolve();
          }
        }, 100);
      }
    });
  }

  async calculateRoute(origin, destination, waypoints = []) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      const request = {
        origin: origin,
        destination: destination,
        waypoints: waypoints.map(wp => ({ location: wp, stopover: true })),
        travelMode: window.google.maps.TravelMode.DRIVING,
        optimizeWaypoints: true,
        avoidHighways: false,
        avoidTolls: false
      };

      this.directionsService.route(request, (result, status) => {
        if (status === 'OK') {
          resolve({
            route: result.routes[0],
            distance: result.routes[0].legs.reduce((total, leg) => total + leg.distance.value, 0),
            duration: result.routes[0].legs.reduce((total, leg) => total + leg.duration.value, 0),
            waypoint_order: result.routes[0].waypoint_order
          });
        } else {
          reject(new Error(`Directions request failed: ${status}`));
        }
      });
    });
  }

  async geocodeAddress(address) {
    await this.initialize();
    
    return new Promise((resolve, reject) => {
      this.geocoder.geocode({ address: address }, (results, status) => {
        if (status === 'OK') {
          const location = results[0].geometry.location;
          resolve({
            lat: location.lat(),
            lng: location.lng(),
            formatted_address: results[0].formatted_address
          });
        } else {
          reject(new Error(`Geocoding failed: ${status}`));
        }
      });
    });
  }

  calculateDistance(point1, point2) {
    const lat1 = point1.lat * Math.PI / 180;
    const lat2 = point2.lat * Math.PI / 180;
    const deltaLat = (point2.lat - point1.lat) * Math.PI / 180;
    const deltaLng = (point2.lng - point1.lng) * Math.PI / 180;

    const a = Math.sin(deltaLat/2) * Math.sin(deltaLat/2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(deltaLng/2) * Math.sin(deltaLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return 6371 * c; // Distance in km
  }
}

export const googleMapsService = new GoogleMapsService();