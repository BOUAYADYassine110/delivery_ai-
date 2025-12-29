import httpx

class DeliveryRouter:
    """Determines if delivery is intra-city or inter-city and routes to appropriate workflow"""
    
    @staticmethod
    async def detect_delivery_type(sender_lat, sender_lng, receiver_lat, receiver_lng):
        """Detect if addresses are in same city or different cities"""
        
        # Calculate distance first
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        dlat = radians(receiver_lat - sender_lat)
        dlon = radians(receiver_lng - sender_lng)
        a = sin(dlat/2)**2 + cos(radians(sender_lat)) * cos(radians(receiver_lat)) * sin(dlon/2)**2
        distance = R * 2 * atan2(sqrt(a), sqrt(1-a))
        
        # If distance < 30km, assume intra-city (same city)
        if distance < 30:
            return {
                "type": "intra_city",
                "sender_city": "Same City",
                "receiver_city": "Same City",
                "distance": distance
            }
        
        # For longer distances, check city names
        try:
            async with httpx.AsyncClient() as client:
                sender_response = await client.get(
                    f"https://nominatim.openstreetmap.org/reverse",
                    params={"lat": sender_lat, "lon": sender_lng, "format": "json"},
                    headers={"User-Agent": "DeliveryApp/1.0"},
                    timeout=3.0
                )
                
                receiver_response = await client.get(
                    f"https://nominatim.openstreetmap.org/reverse",
                    params={"lat": receiver_lat, "lon": receiver_lng, "format": "json"},
                    headers={"User-Agent": "DeliveryApp/1.0"},
                    timeout=3.0
                )
                
                if sender_response.status_code == 200 and receiver_response.status_code == 200:
                    sender_data = sender_response.json()
                    receiver_data = receiver_response.json()
                    
                    sender_city = sender_data.get('address', {}).get('city') or sender_data.get('address', {}).get('town') or "Unknown"
                    receiver_city = receiver_data.get('address', {}).get('city') or receiver_data.get('address', {}).get('town') or "Unknown"
                    
                    is_same_city = sender_city.lower() == receiver_city.lower()
                    
                    return {
                        "type": "intra_city" if is_same_city else "inter_city",
                        "sender_city": sender_city,
                        "receiver_city": receiver_city,
                        "distance": distance
                    }
        except Exception as e:
            print(f"City detection error: {e}")
        
        # Fallback based on distance
        return {
            "type": "inter_city" if distance > 50 else "intra_city",
            "sender_city": "Unknown",
            "receiver_city": "Unknown",
            "distance": distance
        }
    
    @staticmethod
    async def route_order(order_data, delivery_type):
        """Route order to appropriate workflow based on delivery type"""
        
        print(f"Routing order {order_data.get('tracking_number')} to {delivery_type} workflow")
        
        if delivery_type == "intra_city":
            from backend.api.services.intra_city_workflow import IntraCityWorkflow
            workflow = IntraCityWorkflow()
            result = await workflow.process_new_order(order_data)
            print(f"Intra-city workflow completed: {result.get('status')}")
            return result
        else:
            print(f"Inter-city workflow not yet implemented")
            return {
                "status": "pending",
                "message": "Inter-city delivery system coming soon",
                "type": "inter_city"
            }
