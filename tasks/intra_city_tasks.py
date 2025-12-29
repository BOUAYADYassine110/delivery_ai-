from crewai import Task

# Coordinator Tasks
def create_coordinate_workflow_task(agent, order_data):
    return Task(
        description=f"Coordinate the entire delivery workflow for order: {order_data}. Orchestrate all agents to ensure smooth delivery.",
        expected_output="Workflow coordination status with all agent actions completed",
        agent=agent
    )

# Client Service Tasks
def create_validate_order_task(agent, order_data):
    return Task(
        description=f"Validate order details: {order_data}. Check addresses, contact info, and package details.",
        expected_output="Order validation result with any issues identified",
        agent=agent
    )

def create_send_notification_task(agent, notification_type, order_id):
    return Task(
        description=f"Send {notification_type} notification for order {order_id} to customer",
        expected_output="Notification sent confirmation",
        agent=agent
    )

# Pricing Tasks
def create_calculate_price_task(agent, order_data):
    return Task(
        description=f"Calculate delivery price for: distance={order_data.get('distance')}km, weight={order_data.get('weight')}kg, service={order_data.get('service_type')}",
        expected_output="Final price with breakdown",
        agent=agent
    )

# Smart Routing Tasks
def create_calculate_route_task(agent, pickup, delivery):
    return Task(
        description=f"Calculate optimal route from {pickup} to {delivery}. Use OSRM API for real road routing.",
        expected_output="Route with coordinates, distance, and duration",
        agent=agent
    )

def create_monitor_route_task(agent, order_id, route_data):
    return Task(
        description=f"Monitor traffic and weather conditions for order {order_id} route. Check every 5 minutes and suggest rerouting if needed.",
        expected_output="Route monitoring status with any alerts or reroute suggestions",
        agent=agent
    )

def create_reroute_task(agent, order_id, current_location, destination):
    return Task(
        description=f"Calculate new optimal route for order {order_id} from current location {current_location} to {destination} due to traffic/weather changes",
        expected_output="New route with updated ETA",
        agent=agent
    )

# Courier Management Tasks
def create_assign_courier_task(agent, order_data):
    return Task(
        description=f"Find and assign best available courier for order near {order_data.get('pickup_location')}. Consider distance, vehicle type, and current load.",
        expected_output="Assigned courier ID with details",
        agent=agent
    )

def create_track_courier_task(agent, courier_id, order_id):
    return Task(
        description=f"Track courier {courier_id} location for order {order_id} and update database every 10 seconds",
        expected_output="Courier location tracking status",
        agent=agent
    )

def create_verify_delivery_task(agent, order_id, proof_data):
    return Task(
        description=f"Verify delivery completion for order {order_id}. Check proof: {proof_data}",
        expected_output="Delivery verification result",
        agent=agent
    )

# Tracking & Monitoring Tasks
def create_broadcast_location_task(agent, order_id, location):
    return Task(
        description=f"Broadcast location update for order {order_id}: {location} to all connected customers via WebSocket",
        expected_output="Broadcast confirmation",
        agent=agent
    )

def create_update_eta_task(agent, order_id, current_location, destination):
    return Task(
        description=f"Calculate updated ETA for order {order_id} from {current_location} to {destination}",
        expected_output="Updated ETA in minutes",
        agent=agent
    )

def create_generate_analytics_task(agent, time_period):
    return Task(
        description=f"Generate delivery analytics for {time_period}: total deliveries, average time, success rate, courier performance",
        expected_output="Analytics report with key metrics",
        agent=agent
    )
