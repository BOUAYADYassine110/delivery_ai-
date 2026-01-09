"""
AI Pricing Integration Module
Integrates CrewAI pricing agent into order creation and pricing calculations
"""

async def calculate_ai_price(weight: float, distance: float, service_type: str, is_inter_city: bool):
    """
    Calculate price using AI agent with fallback to formula
    
    Args:
        weight: Package weight in kg
        distance: Distance in km
        service_type: 'standard' or 'express'
        is_inter_city: Boolean indicating if inter-city delivery
    
    Returns:
        dict with price, method, and optional ai_analysis
    """
    try:
        from api.services.agent_service import AgentService
        
        # Try AI pricing first
        ai_result = await AgentService.calculate_price(weight, distance, service_type)
        if ai_result and 'price' in ai_result:
            # Adjust AI price based on delivery type
            base_ai_price = ai_result['price']
            
            if is_inter_city:
                # Scale up for inter-city
                adjusted_price = base_ai_price * 2.5 + distance * 0.6
            else:
                # Keep intra-city reasonable
                adjusted_price = base_ai_price * 1.2
            
            service_multiplier = {'standard': 1.0, 'express': 1.5}.get(service_type, 1.0)
            final_price = adjusted_price * service_multiplier
            
            return {
                'price': round(final_price, 2),
                'method': 'ai_agent',
                'ai_analysis': ai_result.get('ai_analysis', 'AI-powered pricing calculation')
            }
    except Exception as e:
        print(f"AI pricing failed: {e}")
    
    # Fallback to formula-based pricing
    if is_inter_city:
        base_price = 50.0
        distance_cost = distance * 0.6
        weight_cost = weight * 4.0
    else:
        base_price = 15.0
        distance_cost = 10.0
        weight_cost = weight * 2.0
    
    service_multiplier = {'standard': 1.0, 'express': 1.5}.get(service_type, 1.0)
    fallback_price = (base_price + distance_cost + weight_cost) * service_multiplier
    
    return {
        'price': round(fallback_price, 2),
        'method': 'formula',
        'ai_analysis': None
    }
