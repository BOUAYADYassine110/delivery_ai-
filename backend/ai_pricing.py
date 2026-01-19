"""
AI Pricing Integration Module
Integrates CrewAI pricing agent into order creation and pricing calculations
"""
from api.agents.pricing_agent import PricingAgent

price_agent = PricingAgent()

async def calculate_ai_price(weight: float, distance: float, service_type: str, is_inter_city: bool):
    """
    Calculate price using AI agent with fallback to formula - MOROCCAN MARKET RATES
    
    Args:
        weight: Package weight in kg
        distance: Distance in km
        service_type: 'standard' or 'express'
        is_inter_city: Boolean indicating if inter-city delivery
    
    Returns:
        dict with price, method, and optional ai_analysis
    """
    try:
        # Try AI pricing first
        ai_result = await price_agent.calculate_price(weight, distance, service_type)
        if ai_result and 'price' in ai_result:
            # Adjust AI price based on delivery type - MOROCCAN RATES
            base_ai_price = ai_result['price']
            
            if is_inter_city:
                # Reasonable inter-city pricing for Morocco
                adjusted_price = base_ai_price * 0.8 + distance * 0.3  # 0.3 MAD per km
            else:
                # Keep intra-city reasonable
                adjusted_price = base_ai_price * 1.0
            
            service_multiplier = {'standard': 1.0, 'express': 1.3}.get(service_type, 1.0)
            final_price = adjusted_price * service_multiplier
            
            return {
                'price': round(final_price, 2),
                'method': 'ai_agent',
                'ai_analysis': ai_result.get('ai_analysis', 'AI-powered pricing calculation')
            }
    except Exception as e:
        print(f"AI pricing failed: {e}")
    
    # Fallback to formula-based pricing - MOROCCAN RATES
    if is_inter_city:
        base_price = 30.0  # MAD
        distance_cost = distance * 0.3  # 0.3 MAD per km
        weight_cost = weight * 2.0  # 2 MAD per kg
    else:
        base_price = 15.0  # MAD
        distance_cost = 10.0
        weight_cost = weight * 2.0
    
    service_multiplier = {'standard': 1.0, 'express': 1.3}.get(service_type, 1.0)
    fallback_price = (base_price + distance_cost + weight_cost) * service_multiplier
    
    return {
        'price': round(fallback_price, 2),
        'method': 'formula',
        'ai_analysis': None
    }
