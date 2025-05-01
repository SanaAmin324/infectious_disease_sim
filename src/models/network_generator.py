import networkx as nx
import numpy as np
import random
import json
import os

def generate_social_network(num_nodes=100, k=4, rewiring_prob=0.1, area_size=800):
    """
    Generates a Watts-Strogatz small-world network and assigns physical properties to each node.
    """
    # Generate a Watts-Strogatz graph
    G = nx.watts_strogatz_graph(n=num_nodes, k=k, p=rewiring_prob)

    # Assign initial properties to nodes
    for node in G.nodes():
        # Initial health status
        G.nodes[node]['status'] = 'healthy'
        G.nodes[node]['infection_timer'] = 0
        G.nodes[node]['infection_type'] = None  # 'asymptomatic' or 'symptomatic'

        # Random position and velocity in 2D space
        x, y = random.randint(0, area_size), random.randint(0, area_size)
        vx, vy = random.uniform(-1, 1), random.uniform(-1, 1)

        G.nodes[node]['position'] = np.array([x, y], dtype=float)
        G.nodes[node]['velocity'] = np.array([vx, vy], dtype=float)

    return G

def save_network_to_file(G, filename="network.json"):
    """Save the generated network to a JSON file."""
    # Prepare data for saving
    network_data = {
        'nodes': [],
        'edges': list(G.edges())
    }

    for node, data in G.nodes(data=True):
        network_data['nodes'].append({
            'id': node,
            'status': data['status'],
            'position': data['position'].tolist(),
            'velocity': data['velocity'].tolist(),
            'infection_timer': data['infection_timer'],
            'infection_type': data['infection_type']
        })

    # Create data folder if it doesn't exist
    os.makedirs("data/graphs", exist_ok=True)

    # Save the data as a JSON file
    with open(f"data/graphs/{filename}", "w") as f:
        json.dump(network_data, f, indent=4)

    print(f"Network saved to data/graphs/{filename}")

if __name__ == "__main__":
    # Generate a social network
    G = generate_social_network()

    # Save it to a file
    save_network_to_file(G)
