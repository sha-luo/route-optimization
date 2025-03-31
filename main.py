from network import Network, Node
import pandas as pd
from optimization import solve_master_problem, solve_subproblem, find_integer_solution
from visualize import visualize_network, visualize_route
from postprocessing import validate_solution
import matplotlib.pyplot as plt
from config import load_config



def main():
    # Load configuration
    config = load_config()
    
    # Set up logging
    log_file = open(config['output']['info_log'], 'w')
    
    # read locations
    log_file.write("Reading locations from file...\n")
    locations_df = pd.read_csv(config['input']['locations_file'])
    # read demand
    demand = pd.read_csv(config['input']['demand_file'])

    # Create network
    log_file.write("Creating network...\n")
    nodes = {
        row['name']: Node.from_csv_row(row['name'], row['latitude'], row['longitude']) 
        for _, row in locations_df.iterrows()
    }
    
    network = Network(nodes, demand)
    # network.max_empty_miles = config['model']['max_empty_miles']  # Set max empty miles

    # Start column generation
    log_file.write("Starting column generation...\n")
    optimal_values = []
    
    for iter in range(config['model']['max_iterations']):
        log_file.write(f"========================================== Iteration {iter} ==========================================\n")
        optimal_value, _ = solve_master_problem(network)
        optimal_values.append(optimal_value)
        log_file.write(f'optimal_value: {optimal_value}\n')
        r = solve_subproblem(network)
        if r is not None:
            network.add_route(r)
            log_file.write(f'route added: {r}\n')
        else:
            log_file.write('No negative reduced cost cycle found\n')
            break

    optimal_value, optimal_routes = find_integer_solution(network)
    log_file.write(f"==================================================================================================\n")
    log_file.write("Found integer solution\n")
    log_file.write(f'optimization value: {optimal_value}\n')
    
    # Close log file
    log_file.close()
    
    # Write optimal routes to file
    with open(config['output']['routes_file'], 'w') as f:
        for r, value in optimal_routes.items():
            f.write(f'{r}: {value:.2f}\n')

    # check if the solution satisfies all the demands
    validate_solution(network, optimal_routes)

    # visualize the network
    visualize_network(network)

    # visualize the routes
    visualize_route(network, 'dc0_store0_vendor2_dc2_store16_vendor8_store17_vendor0_store10_vendor6_dc0')

    # plot optimal values and save to file
    plt.figure(figsize=(config['model']['visualization']['figure_width'], 
                       config['model']['visualization']['figure_height']))
    plt.plot(range(len(optimal_values)), optimal_values, marker='o')
    plt.title('Optimal Values vs. Iterations')
    plt.xlabel('Iteration')
    plt.ylabel('Optimal Value')
    plt.grid(True)
    plt.savefig(config['output']['optimal_values_plot'])
    plt.close()

if __name__ == "__main__":
    main()