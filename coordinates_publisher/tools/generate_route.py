import argparse
import requests
import csv

# Function to fetch route data from OSRM API
def fetch_route_data(source, destination):
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{source};{destination}?steps=true&geometries=geojson&overview=false"
    response = requests.get(osrm_url)
    return response.json()

# Function to process the OSRM route data and extract coordinates
def extract_coordinates(route_data):
    lat_long_pairs = []
    for step in route_data['routes'][0]['legs'][0]['steps']:
        for coord in step['geometry']['coordinates']:
            lat_long_pairs.append((coord[1], coord[0]))  # Convert to (latitude, longitude)
    return lat_long_pairs

# Function to save coordinates to a CSV file
def save_to_csv(lat_long_pairs, output_file):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['latitude', 'longitude'])
        writer.writerows(lat_long_pairs)

# Main function
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate route with latitude and longitude coordinates.')
    parser.add_argument('source_lat', type=float, help='Source latitude')
    parser.add_argument('source_lon', type=float, help='Source longitude')
    parser.add_argument('dest_lat', type=float, help='Destination latitude')
    parser.add_argument('dest_lon', type=float, help='Destination longitude')
    parser.add_argument('--output' ,type=str, required=True, help='Output CSV file name')

    # Parse arguments
    args = parser.parse_args()
    source = f"{args.source_lon},{args.source_lat}"
    destination = f"{args.dest_lon},{args.dest_lat}"
    output_file = args.output

    # Fetch route data from OSRM
    route_data = fetch_route_data(source, destination)

    # Extract coordinates from route data
    lat_long_pairs = extract_coordinates(route_data)

    # Save coordinates to CSV
    save_to_csv(lat_long_pairs, output_file)
    print(f"Coordinates have been successfully exported to {output_file}")

if __name__ == '__main__':
    main()