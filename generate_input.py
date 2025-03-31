import argparse
import geopandas as gpd
from shapely.geometry import Point
import random
import pandas as pd
import numpy as np
from network import Network, Node

def random_us_coordinates():
    # Load USA shapefile from GeoPandas
    ## TODO: move to config
    shapefile_path = "ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp"
    gdf = gpd.read_file(shapefile_path)
    usa = gdf[gdf['NAME'] == 'United States of America']
    
    while True:
        lat = random.uniform(24.396308, 49.384358)
        lon = random.uniform(-125.0, -66.93457)
        point = Point(lon, lat)
        if usa.contains(point).any():
            return lon, lat

def generate_locations(args):
    
    locations = []   
    entities = {
        'vendor': args.vendor,
        'store': args.store,
        'dc': args.distribution_center
    }
  
    for k, v in entities.items():
        for i in range(v):
            lon, lat = random_us_coordinates()
            locations.append({
                'name': f'{k}{i}',
                'latitude': lat,
                'longitude': lon
            })
    return locations

def generate_demand(args):
    demand = []
    demand_types = ['dc_to_store', 'vendor_to_dc', 'vendor_to_store']
    probabilities = [0.45, 0.45, 0.1]  # move to config

    samples = np.random.choice(demand_types, size=200, p=probabilities)
    df = pd.DataFrame(samples, columns=['demand_type'])
    df['origin'] = df['demand_type'].str.split('_to_').str[0]
    df['destination'] = df['demand_type'].str.split('_to_').str[1]
    df['origin_id'] = df['origin'].apply(lambda x: 
        random.randint(0, args.distribution_center - 1) if x == 'dc'
        else random.randint(0, args.vendor - 1) if x == 'vendor'
        else random.randint(0, args.store - 1)
    )
    df['destination_id'] = df['destination'].apply(lambda x: 
        random.randint(0, args.distribution_center - 1) if x == 'dc'
        else random.randint(0, args.vendor - 1) if x == 'vendor'
        else random.randint(0, args.store - 1)
    )
    df['origin'] = df['origin'] + df['origin_id'].astype(str)
    df['destination'] = df['destination'] + df['destination_id'].astype(str)
    df.drop(columns=['origin_id', 'destination_id'], inplace=True)

    df['demand'] = np.random.randint(1, 100, size=len(df)) # move to config

    # Aggregate demand by demand_type, origin, and destination
    aggregated_df = df.groupby(['demand_type', 'origin', 'destination'])['demand'].sum().reset_index()

    return aggregated_df
    
    
def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process vendor, store, and distribution center counts'
    )
    
    parser.add_argument(
        '-v', '--vendor',
        type=int,
        required=True,
        help='Number of vendors'
    )
    
    parser.add_argument(
        '-s', '--store',
        type=int,
        required=True,
        help='Number of stores'
    )
    
    parser.add_argument(
        '-d', '--distribution_center',
        type=int,
        required=True,
        help='Number of distribution centers'
    )

    parser.add_argument(
        '-m', '--max_empty_miles',
        type=int,
        default=200,
        help='Maximum distance for traveling empty miles'
    )
    
    return parser.parse_args()


def main():

    args = parse_arguments()
    
    # Generate locations for store, vendor, and distribution center
    locations = generate_locations(args)
    locations_df = pd.DataFrame(locations)
    locations_df.to_csv('input/locations.csv', index=False)

    # Generate demand for each location
    demand = generate_demand(args)
    demand.to_csv('input/demand.csv', index=False)

        
   

if __name__ == "__main__":
    main()