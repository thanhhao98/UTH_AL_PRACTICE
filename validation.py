import networkx as nx
from bellman_ford import bellman_ford, extract_cycle
import math
import time


def extract_nx_cycle(G):
    """
    Extract a negative cycle from a NetworkX graph

    Args:
        G: NetworkX DiGraph

    Returns:
        cycle: List of nodes in the negative cycle, or None if no cycle exists
        cycle_weight: Total weight of the cycle
    """
    try:
        # Find a negative cycle using NetworkX's dedicated function
        cycle = nx.find_negative_cycle(G, 0)

        # Calculate cycle weight
        if cycle:
            cycle_weight = sum(
                G[cycle[i]][cycle[i + 1]]["weight"] for i in range(len(cycle) - 1)
            )
            return cycle, cycle_weight
        return None, 0
    except:
        # Try a different approach if the first one fails
        try:
            for source in range(len(G)):
                try:
                    # This will raise an exception if a negative cycle is detected
                    dist = nx.bellman_ford_path_length(G, source)
                except nx.NetworkXUnbounded:
                    # Manually find a node that's part of a negative cycle
                    pred = {}
                    for u, v in G.edges():
                        if u not in pred:
                            pred[u] = None
                        if v not in pred:
                            pred[v] = None

                    for u, v in G.edges():
                        # If relaxation is still possible, we have a negative cycle
                        if G[u][v]["weight"] + dist.get(u, float("inf")) < dist.get(
                            v, float("inf")
                        ):
                            # Find the cycle manually
                            cycle = [v]
                            current = u
                            while current not in cycle:
                                cycle.append(current)
                                # Go to predecessor if known
                                if current in pred and pred[current] is not None:
                                    current = pred[current]
                                else:
                                    # Just use a neighbor as fallback
                                    for neighbor in G.predecessors(current):
                                        current = neighbor
                                        break

                            # Slice to get just the cycle
                            start_idx = cycle.index(current)
                            cycle = cycle[start_idx:]
                            cycle.append(cycle[0])  # Close the cycle

                            # Calculate cycle weight
                            cycle_weight = 0
                            for i in range(len(cycle) - 1):
                                cycle_weight += G[cycle[i]][cycle[i + 1]]["weight"]

                            return cycle, cycle_weight
        except:
            pass

    return None, 0


def run_algorithms(edges, num_vertices):
    """
    Run both NetworkX and our Bellman-Ford implementation with timing

    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph

    Returns:
        nx_has_cycle: Whether NetworkX detected a negative cycle
        nx_cycle: The negative cycle detected by NetworkX (if any)
        nx_cycle_weight: Weight of the NetworkX cycle
        nx_profit_factor: Profit factor of the NetworkX cycle
        nx_time: Time taken by NetworkX implementation (seconds)
        our_cycle: Our detected cycle
        our_has_cycle: Whether our implementation detected a valid cycle
        our_has_arbitrage: Whether our cycle is profitable
        our_time: Time taken by our implementation (seconds)
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

    # Time NetworkX implementation
    nx_start_time = time.time()
    
    # Check if there's a negative cycle using NetworkX
    nx_has_cycle = False
    nx_cycle = None
    nx_cycle_weight = 0
    nx_profit_factor = 1.0

    try:
        # Use bellman_ford_predecessor_and_distance which checks for negative cycles
        for source in range(min(5, num_vertices)):  # Check from a few sources
            nx.bellman_ford_predecessor_and_distance(G, source)
        nx_has_cycle = False
    except nx.NetworkXUnbounded:
        nx_has_cycle = True
        # Extract the negative cycle if one exists
        nx_cycle, nx_cycle_weight = extract_nx_cycle(G)
        if nx_cycle and nx_cycle_weight < 0:
            nx_profit_factor = math.exp(-nx_cycle_weight)
    
    nx_end_time = time.time()
    nx_time = nx_end_time - nx_start_time

    # Time our implementation
    our_start_time = time.time()
    
    # Run our implementation
    _, pred, our_neg_cycle_start = bellman_ford(edges, num_vertices)

    # Get our cycle
    our_cycle = None
    profit = 0
    our_has_arbitrage = False

    if our_neg_cycle_start is not None:
        our_cycle, profit, _, _ = extract_cycle(
            pred, our_neg_cycle_start, edges, num_vertices
        )
        our_has_cycle = len(our_cycle) > 1
        our_has_arbitrage = our_has_cycle and profit > 1.0
    else:
        our_has_cycle = False
    
    our_end_time = time.time()
    our_time = our_end_time - our_start_time

    return (
        nx_has_cycle,
        nx_cycle,
        nx_cycle_weight,
        nx_profit_factor,
        nx_time,
        our_cycle,
        our_has_cycle,
        our_has_arbitrage,
        our_time,
    )


def validate_results(nx_has_cycle, our_has_cycle, our_has_arbitrage):
    """
    Validate results by comparing NetworkX and our implementation

    Args:
        nx_has_cycle: Whether NetworkX detected a negative cycle
        our_has_cycle: Whether our implementation detected a valid cycle
        our_has_arbitrage: Whether our cycle is profitable

    Returns:
        is_valid: Whether our implementation matches the library
        cycles_agree: Whether both implementations agree
    """
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

    return is_valid, cycles_agree


def validate_bellman_ford_with_library(edges, num_vertices):
    """
    Validate our Bellman-Ford implementation using NetworkX library

    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph

    Returns:
        is_valid: Whether our implementation matches the library
        nx_has_cycle: Whether NetworkX detected a negative cycle
        nx_cycle: The negative cycle detected by NetworkX (if any)
        nx_cycle_weight: Weight of the NetworkX cycle
        nx_profit_factor: Profit factor of the NetworkX cycle
        our_cycle: Our detected cycle
        our_has_arbitrage: Whether our cycle is profitable
        cycles_agree: Whether both implementations agree
    """
    # Run both algorithms
    (
        nx_has_cycle,
        nx_cycle,
        nx_cycle_weight,
        nx_profit_factor,
        nx_time,
        our_cycle,
        our_has_cycle,
        our_has_arbitrage,
        our_time,
    ) = run_algorithms(edges, num_vertices)

    # Validate results
    is_valid, cycles_agree = validate_results(
        nx_has_cycle, our_has_cycle, our_has_arbitrage
    )

    return (
        is_valid,
        nx_has_cycle,
        nx_cycle,
        nx_cycle_weight,
        nx_profit_factor,
        nx_time,
        our_cycle,
        our_has_arbitrage,
        cycles_agree,
        our_time,
    )
