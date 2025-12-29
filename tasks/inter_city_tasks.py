from crewai import Task

# Inter-City Coordinator Tasks
def create_coordinate_inter_city_workflow_task(agent, order_data):
    return Task(
        description=f"Coordinate the entire inter-city delivery workflow for order: {order_data}. Orchestrate all agents across multiple cities.",
        expected_output="Inter-city workflow coordination status with all agent actions completed",
        agent=agent
    )

# Inter-City Client Service Tasks
def create_validate_inter_city_order_task(agent, order_data):
    return Task(
        description=f"Validate inter-city order details: {order_data}. Check addresses across cities, contact info, and package details.",
        expected_output="Inter-city order validation result with any issues identified",
        agent=agent
    )

def create_send_inter_city_notification_task(agent, notification_type, order_id):
    return Task(
        description=f"Send {notification_type} notification for inter-city order {order_id} to customer with multi-city updates",
        expected_output="Inter-city notification sent confirmation",
        agent=agent
    )

# Inter-City Pricing Tasks
def create_calculate_inter_city_price_task(agent, order_data):
    return Task(
        description=f"Calculate inter-city delivery price for: distance={order_data.get('distance')}km, weight={order_data.get('weight')}kg, cities={order_data.get('cities_involved')}, transportation={order_data.get('transportation_mode')}",
        expected_output="Final inter-city price with detailed breakdown including hub fees and transportation costs",
        agent=agent
    )

# Long Distance Routing Tasks
def create_plan_inter_city_route_task(agent, origin_city, destination_city, waypoints=None):
    return Task(
        description=f"Plan optimal inter-city route from {origin_city} to {destination_city}. Consider highways, logistics hubs, and transportation modes. Waypoints: {waypoints}",
        expected_output="Complete inter-city route plan with hubs, transportation segments, and estimated times",
        agent=agent
    )

def create_monitor_inter_city_route_task(agent, order_id, route_data):
    return Task(
        description=f"Monitor inter-city route for order {order_id}. Check weather, traffic, and transportation schedules across all segments.",
        expected_output="Inter-city route monitoring status with any alerts or reroute suggestions",
        agent=agent
    )

# Logistics Hub Tasks
def create_assign_logistics_hubs_task(agent, route_plan):
    return Task(
        description=f"Assign appropriate logistics hubs for route: {route_plan}. Optimize package sorting and transfer points.",
        expected_output="Assigned logistics hubs with transfer schedules",
        agent=agent
    )

def create_coordinate_hub_transfers_task(agent, order_id, hub_sequence):
    return Task(
        description=f"Coordinate package transfers through hubs: {hub_sequence} for order {order_id}",
        expected_output="Hub transfer coordination status and schedules",
        agent=agent
    )

# Transportation Coordinator Tasks
def create_assign_transportation_task(agent, route_segments):
    return Task(
        description=f"Assign transportation for route segments: {route_segments}. Choose optimal vehicles and schedules.",
        expected_output="Assigned transportation with schedules and vehicle details",
        agent=agent
    )

def create_monitor_transportation_task(agent, order_id, transportation_plan):
    return Task(
        description=f"Monitor transportation progress for order {order_id} across all segments: {transportation_plan}",
        expected_output="Transportation monitoring status with delays or issues",
        agent=agent
    )

# Warehouse Coordinator Tasks
def create_manage_warehouse_operations_task(agent, order_id, warehouse_sequence):
    return Task(
        description=f"Manage warehouse operations for order {order_id} through warehouses: {warehouse_sequence}",
        expected_output="Warehouse operations status and package handling details",
        agent=agent
    )

def create_schedule_warehouse_transfers_task(agent, order_id, transfer_schedule):
    return Task(
        description=f"Schedule warehouse transfers for order {order_id}: {transfer_schedule}",
        expected_output="Warehouse transfer schedule confirmation",
        agent=agent
    )

# Customs Clearance Tasks
def create_handle_customs_clearance_task(agent, order_data):
    return Task(
        description=f"Handle customs clearance for international segments in order: {order_data}",
        expected_output="Customs clearance status and documentation details",
        agent=agent
    )

def create_verify_customs_compliance_task(agent, order_id, customs_data):
    return Task(
        description=f"Verify customs compliance for order {order_id}: {customs_data}",
        expected_output="Customs compliance verification result",
        agent=agent
    )

# Inter-City Tracking Tasks
def create_track_inter_city_package_task(agent, order_id, route_segments):
    return Task(
        description=f"Track package {order_id} across inter-city route segments: {route_segments}",
        expected_output="Real-time inter-city tracking updates",
        agent=agent
    )

def create_calculate_inter_city_eta_task(agent, order_id, current_segment, remaining_segments):
    return Task(
        description=f"Calculate updated ETA for inter-city order {order_id}. Current segment: {current_segment}, Remaining: {remaining_segments}",
        expected_output="Updated inter-city ETA with detailed breakdown",
        agent=agent
    )

def create_broadcast_inter_city_updates_task(agent, order_id, status_updates):
    return Task(
        description=f"Broadcast inter-city status updates for order {order_id}: {status_updates} to customer",
        expected_output="Inter-city broadcast confirmation",
        agent=agent
    )

# Analytics Tasks
def create_generate_inter_city_analytics_task(agent, time_period):
    return Task(
        description=f"Generate inter-city delivery analytics for {time_period}: cross-city performance, hub efficiency, transportation metrics",
        expected_output="Inter-city analytics report with key metrics",
        agent=agent
    )
