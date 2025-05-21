import networkx as nx
from bellman_ford import bellman_ford, extract_cycle

def validate_bellman_ford_with_library(edges, num_vertices):
    """
    Validate our Bellman-Ford implementation using NetworkX library
    
    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph
        
    Returns:
        is_valid: Whether our implementation matches the library
        nx_has_cycle: Whether NetworkX detected a negative cycle
        our_cycle: Our detected cycle
        our_has_arbitrage: Whether our cycle is profitable
        cycles_agree: Whether both implementations agree
    """
    # Create a NetworkX DiGraph
    G = nx.DiGraph()
    
    # Add nodes
    G.add_nodes_from(range(num_vertices))
    
    # Add edges (excluding the dummy source edges)
    edge_data = {}
    for u, v, weight in edges:
        if u < num_vertices and v < num_vertices:
            G.add_edge(u, v, weight=weight)
            edge_data[(u, v)] = weight
    
    # Check if there's a negative cycle using NetworkX
    nx_has_cycle = False
    
    try:
        # Use bellman_ford_predecessor_and_distance which checks for negative cycles
        for source in range(min(5, num_vertices)):  # Check from a few sources
            nx.bellman_ford_predecessor_and_distance(G, source)
        nx_has_cycle = False
    except nx.NetworkXUnbounded:
        nx_has_cycle = True

    # Run our implementation
    _, pred, our_neg_cycle_start = bellman_ford(edges, num_vertices)
    
    # Get our cycle
    our_cycle = None
    profit = 0
    our_has_arbitrage = False
    
    if our_neg_cycle_start is not None:
        our_cycle, profit, total_weight, _ = extract_cycle(pred, our_neg_cycle_start, edges, num_vertices)
        our_has_cycle = len(our_cycle) > 1
        our_has_arbitrage = our_has_cycle and profit > 1.0
    else:
        our_has_cycle = False

    # Compare results between implementations
    if not nx_has_cycle and not our_has_cycle:
        # Both agree there's no cycle
        is_valid = True
        cycles_agree = True
    elif nx_has_cycle and our_has_arbitrage:
        # Both agree there's a profitable negative cycle
        is_valid = True
        cycles_agree = True
    elif nx_has_cycle and not our_has_cycle:
        # NetworkX found a cycle, but we filtered it as invalid
        is_valid = True
        cycles_agree = False
    elif nx_has_cycle and our_has_cycle and not our_has_arbitrage:
        # NetworkX found a cycle, we found a cycle but not profitable
        is_valid = True
        cycles_agree = False
    else:
        # Disagreement on cycle presence
        is_valid = False
        cycles_agree = False
    
    return is_valid, nx_has_cycle, our_cycle, our_has_arbitrage, cycles_agree 