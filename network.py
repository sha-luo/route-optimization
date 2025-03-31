from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
from geopy.distance import geodesic
import pandas as pd
import argparse

class LocationType(Enum):
    VENDOR = "vendor"
    STORE = "store"
    DC = "dc"

@dataclass
class Node:
    name: str
    latitude: float
    longitude: float
    location_type: LocationType
    incoming_edges: List['Edge']
    outgoing_edges: List['Edge']

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name

    @classmethod
    def from_csv_row(cls, name: str, latitude: str, longitude: str) -> 'Node':
        # Determine location type from prefix
        if name.startswith('vendor'):
            loc_type = LocationType.VENDOR
        elif name.startswith('store'):
            loc_type = LocationType.STORE
        elif name.startswith('dc'):
            loc_type = LocationType.DC
        else:
            raise ValueError(f"Unknown location type for name: {name}")
        
        return cls(
            name=name,
            latitude=float(latitude),
            longitude=float(longitude),
            location_type=loc_type,
            incoming_edges=[],
            outgoing_edges=[]
        )
    

# Example usage:
def load_locations(csv_path: str) -> List[Node]:
    locations = []
    with open(csv_path, 'r') as f:
        next(f)  # Skip header row
        for line in f:
            name, lat, lon = line.strip().split(',')
            locations.append(Node.from_csv_row(name, lat, lon))
    return locations


class Edge:
    name: str
    origin: Node
    destination: Node
    distance: float
    dual_value: float
    demand: int
    routes: List[int]

    def __init__(self, origin: Node, destination: Node, demand: int):
        self.name = f"{origin.name}_{destination.name}"
        self.origin = origin
        self.destination = destination
        self.distance = self.calculate_distance()
        self.demand = demand
        self.routes = []
        self.dual_value = 0
        
    def calculate_distance(self):
        return geodesic((self.origin.latitude, self.origin.longitude), (self.destination.latitude, self.destination.longitude)).miles
    
    def add_route(self, route: int):
        self.routes.append(route)

    def remove_route(self, route: int):
        self.routes.remove(route)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Route:
    id: int
    n_segments: int
    path: List[Node]
    distance: float

    def __init__(self, path: List[Node]):
        # check if the route is a cycle
        if path[0] != path[-1]:
            raise ValueError("Route is not a cycle")
        
        self.path = path
        self.distance = self.calculate_distance()
        self.n_segments = len(path) - 1

    def __str__(self):
        return f"{'_'.join([n.name for n in self.path])}"
    
    def __repr__(self):
        return f"Route {self.id}: {self.path} Distance: {self.distance}"

    def calculate_distance(self):
        distance = 0
        for i in range(len(self.path) - 1):
            origin = self.path[i]
            destination = self.path[i + 1]
            distance += geodesic((origin.latitude, origin.longitude), (destination.latitude, destination.longitude)).miles
        return distance
    

class Network:
    nodes: Dict[str, Node]
    edges: Dict[str, Edge]
    routes: List[Route]

    def __init__(self, nodes: Dict[str, Node], demand: pd.DataFrame):
        self.demand = demand
        self.nodes = nodes
        self.edges = {}
        self.routes = []
        self.dcs = {node.name: node for node in self.nodes.values() if node.location_type == LocationType.DC}
        self._closest_dcs = {}

        # create connections and initial routes
        self.create_connections(max_empty_miles=2000)
        self.create_initial_routes()
    

    def find_closest_dc(self, node: Node) -> Node:
        """
        Find the closest DC to a given node.
        """
        if node.name in self._closest_dcs:
            return self._closest_dcs[node.name]
        else:
            dcs = [node for node in self.nodes.values() if node.location_type == LocationType.DC]
            closest_dc = min(dcs, key=lambda x: geodesic((node.latitude, node.longitude), (x.latitude, x.longitude)))
            self._closest_dcs[node.name] = closest_dc
            return closest_dc


    def create_connections(self, max_empty_miles: int):
        """
        Our graph is not fully connected. Given the size of the graph, connecting all nodes would unnecessarily increase the size of the problem.
        This function creates the edges and connections between nodes. 
        """

        # Step 1: create edges for each origin and destination in dmenad file
        for index, row in self.demand.iterrows():
            origin = self.nodes[row['origin']]
            destination = self.nodes[row['destination']]
            demand = row['demand']
            edge = Edge(origin, destination, demand)
            # add edge to edges dictionary
            self.edges[edge.name] = edge
            # add edge to origin and destination nodes
            origin.outgoing_edges.append(edge)
            destination.incoming_edges.append(edge)
        
        # Step 2: create artificial edges from stores to vendors to create backhaul opportunities
        stores = [node for node in self.nodes.values() if node.location_type == LocationType.STORE]
        vendors = [node for node in self.nodes.values() if node.location_type == LocationType.VENDOR]

        for store in stores:
            for vendor in vendors:
                distance = geodesic((store.latitude, store.longitude), (vendor.latitude, vendor.longitude)).miles
                if distance <= max_empty_miles:
                    edge = Edge(origin=store, destination=vendor, demand=0)
                    self.edges[edge.name] = edge
                    store.outgoing_edges.append(edge)
                    vendor.incoming_edges.append(edge)


    def create_initial_routes(self):
        """
        Create initial routes for each demand.
        """
        for index, row in self.demand.iterrows():
            demand_type = row['demand_type']
            if demand_type == "dc_to_store":
                dc = self.nodes[row['origin']]
                store = self.nodes[row['destination']]
                route = Route([dc, store, dc])
                self.add_route(route)
            elif demand_type == "vendor_to_dc":
                vendor = self.nodes[row['origin']]
                dc = self.nodes[row['destination']]
                route = Route([dc, vendor, dc])
                self.add_route(route)
            elif demand_type == "vendor_to_store":
                vendor = self.nodes[row['origin']]
                store = self.nodes[row['destination']]
                dc = self.find_closest_dc(vendor)
                route = Route([dc, vendor, store, dc])
                self.add_route(route)
        


    def add_route(self, route: Route):
        """
        Add a route to the network.
        """

        # add route to routes list
        self.routes.append(route)    
        # add route id to each edge in the path
        route.id = len(self.routes) - 1
        for i in range(len(route.path) - 1):
            origin = route.path[i]
            destination = route.path[i + 1]
            edge = self.get_edge(origin, destination)
            edge.add_route(route)

    
    def get_edge(self, origin: Node, destination: Node) -> Edge:
        key = f"{origin.name}_{destination.name}"
        if key in self.edges:
            return self.edges[key] 
        else:
            edge = Edge(origin=origin, destination=destination, demand=0)
            self.edges[key] = edge
            return edge
        
    def reset_dual_value(self):
        for edge in self.edges.values():
            edge.dual_value = 0
    
