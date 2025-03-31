from network import Network, Edge

def validate_solution(network: Network, solution: dict) -> bool:
    """
    Validates if the solution satisfies all demands in the network.
    
    Parameters:
    - network: Network object containing nodes, edges, and routes
    - solution: Dictionary mapping routes to their integer frequencies
    
    Returns:
    - bool: True if all demands are satisfied, False otherwise
    - dict: Dictionary of edges with their satisfied vs required demand
    """
    # Initialize satisfied demand for each edge
    satisfied_demand = {e: 0 for e in network.edges.values()}
    
    # Calculate satisfied demand for each edge based on routes
    for route, frequency in solution.items():
        # Get sequence of nodes in the route
        nodes = route.path
        
        # Check each consecutive pair of nodes in the route
        for i in range(len(nodes) - 1):
            edge = network.get_edge(nodes[i], nodes[i+1])
            if edge in satisfied_demand:
                satisfied_demand[edge] += frequency

    # Check if all demands are met
    validation_results = {}
    all_satisfied = True
    
    for _, edge in network.edges.items():
        if edge.demand > 0:  # Only check edges with positive demand
            is_satisfied = satisfied_demand[edge] >= edge.demand - 1e-6
            validation_results[edge] = {
                'required': edge.demand,
                'satisfied': satisfied_demand[edge],
                'is_satisfied': is_satisfied
            }
            if not is_satisfied:
                all_satisfied = False

    # Print validation results
    if all_satisfied:
        print("All demands are satisfied")
    else:
        print("\nDemand Satisfaction Check:")
        print("==========================")
        for edge, result in validation_results.items():
            if not result['is_satisfied']:
                print(f"Edge {edge.origin.name} -> {edge.destination.name}:")
                print(f"  Required demand: {result['required']}")
                print(f"  Satisfied demand: {result['satisfied']}")
                print(f"  Satisfied?: {'Yes' if result['is_satisfied'] else 'No'}")
                print("---------------------------")

    return all_satisfied, validation_results