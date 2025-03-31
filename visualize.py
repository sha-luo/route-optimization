import folium
from typing import Optional
from network import Network, LocationType
from config import load_config

def visualize_network(network: Network, save_path: Optional[str] = None):
    """
    Creates an interactive map visualization of the network nodes and edges.
    
    Parameters:
    - network: Network object containing nodes and edges
    - save_path: Path to save the HTML map file (if None, uses path from config)
    """
    # Use config path if none provided
    if save_path is None:
        config = load_config()
        save_path = config['output']['network_viz_file']
    
    # Create a map centered on the mean coordinates of all nodes
    center_lat = sum(node.latitude for node in network.nodes.values()) / len(network.nodes)
    center_lon = sum(node.longitude for node in network.nodes.values()) / len(network.nodes)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add nodes to the map
    for node_id, node in network.nodes.items():
        if node.location_type == LocationType.DC:
            color = 'red'
        elif node.location_type == LocationType.STORE:
            color = 'blue'
        elif node.location_type == LocationType.VENDOR:
            color = 'green'
        else:
            color = 'gray'

        tooltip = f"Node {node_id}"
        if node_id in network.dcs:
            tooltip += " (DC)"
            
        folium.CircleMarker(
            location=[node.latitude, node.longitude],
            radius=6,
            color=color,
            fill=True,
            popup=tooltip,
            tooltip=tooltip
        ).add_to(m)
    
    # Add edges to the map
    for edge_id, edge in network.edges.items():
        start_node = network.nodes[edge.origin.name]
        end_node = network.nodes[edge.destination.name]
        
        # Create a line for the edge
        points = [[start_node.latitude, start_node.longitude], [end_node.latitude, end_node.longitude]]
        tooltip = f"{edge.origin} → {edge.destination} (Demand: {edge.demand}) (Distance: {edge.distance:.2f}) (dual: {edge.dual_value:.2f})"
        
        folium.PolyLine(
            points,
            weight=2,
            color='gray',
            opacity=0.8,
            tooltip=tooltip
        ).add_to(m)
    
    # Save the map
    m.save(save_path)
    print(f"Network map saved to {save_path}")


def visualize_route(network: Network, route_str: str, save_path: Optional[str] = "route_map.html"):
    """
    Creates an interactive map visualization of a specific route.
    
    Parameters:
    - network: Network object containing nodes and edges
    - route_str: String representation of the route (node names separated by underscores)
    - save_path: Path to save the HTML map file (default: "route_map.html")
    """
    # Parse the route string into a list of node names
    node_names = route_str.split('_')
    
    # Create a map centered on the mean coordinates of route nodes
    nodes = [network.nodes[name] for name in node_names]
    center_lat = sum(node.latitude for node in nodes) / len(nodes)
    center_lon = sum(node.longitude for node in nodes) / len(nodes)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add nodes to the map with sequence numbers
    for i, node in enumerate(nodes):
        if node.location_type == LocationType.DC:
            color = 'red'
        elif node.location_type == LocationType.STORE:
            color = 'blue'
        elif node.location_type == LocationType.VENDOR:
            color = 'green'
        else:
            color = 'gray'

        # Create tooltip with stop number
        tooltip = f"Stop {i}: {node.name}"
            
        # Add numbered marker
        folium.CircleMarker(
            location=[node.latitude, node.longitude],
            radius=6,
            color=color,
            fill=True,
            popup=tooltip,
            tooltip=tooltip
        ).add_to(m)
        
        # Add stop number label
        folium.map.Marker(
            [node.latitude, node.longitude],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 12pt; color: black;">{i}</div>'
            )
        ).add_to(m)
    
    # Add route segments to the map
    for i in range(len(nodes) - 1):
        start_node = nodes[i]
        end_node = nodes[i + 1]
        
        # Create a line for each segment
        points = [[start_node.latitude, start_node.longitude], 
                 [end_node.latitude, end_node.longitude]]
        tooltip = f"Segment {i}: {start_node.name} → {end_node.name}"

        edge = network.get_edge(start_node, end_node)
        
        # Draw arrow using a colored line
        folium.PolyLine(
            points,
            weight=3,
            color='red',
            opacity=0.8,
            tooltip=tooltip,
            arrow_style='simple',  # Add arrow to show direction
            dash_array='10' if edge and edge.demand == 0 else None  # Make line dashed if no demand
        ).add_to(m)
    
    # Save the map
    m.save(save_path)
    print(f"Route map saved to {save_path}")
