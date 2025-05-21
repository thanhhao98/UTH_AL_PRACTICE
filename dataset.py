import math
import random

def create_dataset(num_currencies=500, num_transactions=100000, insert_cycle=True):
    """
    Generate synthetic exchange rates and transactions between currencies
    
    Args:
        num_currencies: Number of currency nodes
        num_transactions: Number of directed edges (transactions)
        insert_cycle: Whether to insert a known negative cycle
        
    Returns:
        edges: List of tuples (u, v, weight) representing transactions
        num_currencies: Number of currency nodes
    """
    edges = []
    for _ in range(num_transactions):
        u = random.randrange(num_currencies)
        v = random.randrange(num_currencies)
        if u == v:
            continue
        rate = random.uniform(0.5, 2.0)      # random rate between 0.5 and 2.0
        weight = -math.log(rate)            # convert to additive weight
        edges.append((u, v, weight))
    
    # Insert a known negative cycle for demonstration
    if insert_cycle:
        # We need at least 4 currencies for this cycle to work
        if num_currencies < 4:
            print(f"Warning: Inserted cycle requires at least 4 currencies. Using {num_currencies} may result in duplicate nodes.")
        
        # Create a cycle of 4 unique nodes
        node_positions = list(range(min(4, num_currencies)))
        random.shuffle(node_positions)
        
        cycle_nodes = [node_positions[i % len(node_positions)] for i in range(5)]
        cycle_nodes[4] = cycle_nodes[0]  # Close the cycle
        
        rates = [1.05, 0.98, 1.02, 1.03]  # rates whose product >1
        # compute last rate to ensure product=1.05 (profit ~5%)
        product = 1.0
        for r in rates:
            product *= r
        last_rate = 1.05 / product
        rates.append(last_rate)
        
        # Add the cycle edges
        for i in range(len(cycle_nodes)-1):
            u = cycle_nodes[i]
            v = cycle_nodes[i+1]
            if u == v:
                continue  # Skip self-loops if we have too few currencies
            w = -math.log(rates[i])
            edges.append((u, v, w))
    
    return edges, num_currencies 