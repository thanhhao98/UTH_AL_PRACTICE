import math
from rich.table import Table

def bellman_ford(edges, num_vertices):
    """
    Bellman-Ford algorithm implementation to detect negative cycles
    
    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph
        
    Returns:
        dist: Distance array from source
        pred: Predecessor array
        neg_cycle: Starting vertex of negative cycle or None if no cycle exists
    """
    INF = float('inf')
    dist = [INF]*(num_vertices+1)
    pred = [-1]*(num_vertices+1)
    source = num_vertices  # dummy source index
    dist[source] = 0.0
    
    # Connect dummy source to all currencies
    source_edges = [(source, v, 0.0) for v in range(num_vertices)]
    all_edges = edges + source_edges
    
    # Relax edges (V times to check for negative cycle)
    for _ in range(num_vertices):
        updated = False
        for (u, v, w) in all_edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u
                updated = True
        if not updated:
            break
    
    # Check for negative cycle
    neg_cycle_start = None
    for (u, v, w) in all_edges:
        if dist[u] + w < dist[v]:
            neg_cycle_start = v
            break
            
    return dist, pred, neg_cycle_start

def extract_cycle(pred, neg_cycle_start, edges, num_vertices):
    """
    Extract the negative cycle from predecessor array
    
    Args:
        pred: Predecessor array from Bellman-Ford
        neg_cycle_start: Starting vertex of negative cycle
        edges: List of edges
        num_vertices: Number of vertices
        
    Returns:
        cycle: List of vertices in the cycle
        profit: Profit factor for the cycle
        total_weight: Total weight of the cycle
        cycle_rates: Dictionary mapping (from, to) to exchange rate
    """
    # Find actual cycle by following predecessors
    v = neg_cycle_start
    for _ in range(num_vertices):
        v = pred[v] or v
    cycle = []
    start = v
    while True:
        cycle.append(v)
        v = pred[v]
        if v == start or v is None:
            break
    cycle.append(start)
    cycle.reverse()
    
    # Compute total weight and profit factor
    total_weight = 0.0
    cycle_rates = {}
    for i in range(len(cycle)-1):
        # find matching edge weight
        for (u, vv, w) in edges:
            if u == cycle[i] and vv == cycle[i+1]:
                total_weight += w
                # Store the actual exchange rate (inverse of weight)
                rate = math.exp(-w)
                cycle_rates[(u, vv)] = rate
                break
    profit = math.exp(-total_weight)
    
    return cycle, profit, total_weight, cycle_rates

def format_cycle_path(cycle, cycle_rates):
    """Format cycle as a string with exchange rates"""
    if not cycle or len(cycle) < 2:
        return "No cycle"
        
    path_parts = []
    for i in range(len(cycle)-1):
        u, v = cycle[i], cycle[i+1]
        rate = cycle_rates.get((u, v), 0)
        path_parts.append(f"Currency {u} → Currency {v} (rate: {rate:.4f})")
    
    return " → ".join([f"Currency {cycle[0]}"] + [f"Currency {c}" for c in cycle[1:-1]] + [f"Currency {cycle[0]}"])

def create_results_table(cycle, cycle_rates, total_weight, profit):
    """Create a Rich table for detailed results"""
    table = Table(title="Detailed Exchange Path")
    
    table.add_column("From", style="cyan", justify="right")
    table.add_column("To", style="cyan", justify="right")
    table.add_column("Exchange Rate", style="green", justify="right")
    
    for i in range(len(cycle)-1):
        u, v = cycle[i], cycle[i+1]
        rate = cycle_rates.get((u, v), 0)
        table.add_row(f"Currency {u}", f"Currency {v}", f"{rate:.6f}")
    
    return table 