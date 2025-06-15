import time
import random
import statistics
import typer
from typing import List, Tuple, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import track
import networkx as nx
import math

from dataset import create_dataset
from bellman_ford import bellman_ford, extract_cycle
from validation import extract_nx_cycle

console = Console()


def create_random_dataset(num_currencies: int, num_transactions: int, insert_cycle: bool = True) -> Tuple[List[Tuple], int]:
    """
    Create a random dataset for benchmarking
    
    Args:
        num_currencies: Number of currency nodes
        num_transactions: Number of directed edges (transactions)
        insert_cycle: Whether to insert a known negative cycle
        
    Returns:
        edges: List of tuples (u, v, weight) representing transactions
        num_currencies: Number of vertices in the graph
    """
    return create_dataset(num_currencies, num_transactions, insert_cycle)


def run_networkx_benchmark(edges: List[Tuple], num_vertices: int) -> Tuple[bool, List, float, float, float]:
    """
    Run NetworkX Bellman-Ford implementation with timing
    
    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph
        
    Returns:
        has_cycle: Whether a negative cycle was detected
        cycle: The negative cycle (if any)
        cycle_weight: Weight of the cycle
        profit_factor: Profit factor of the cycle
        execution_time: Time taken in seconds
    """
    # Create NetworkX DiGraph
    G = nx.DiGraph()
    G.add_nodes_from(range(num_vertices))
    
    # Add edges
    for u, v, weight in edges:
        if u < num_vertices and v < num_vertices:
            G.add_edge(u, v, weight=weight)
    
    # Time NetworkX implementation
    start_time = time.time()
    
    has_cycle = False
    cycle = None
    cycle_weight = 0
    profit_factor = 1.0
    
    try:
        # Check for negative cycles
        for source in range(min(5, num_vertices)):
            nx.bellman_ford_predecessor_and_distance(G, source)
        has_cycle = False
    except nx.NetworkXUnbounded:
        has_cycle = True
        # Extract the negative cycle if one exists
        cycle, cycle_weight = extract_nx_cycle(G)
        if cycle and cycle_weight < 0:
            profit_factor = math.exp(-cycle_weight)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return has_cycle, cycle, cycle_weight, profit_factor, execution_time


def run_our_implementation_benchmark(edges: List[Tuple], num_vertices: int) -> Tuple[bool, List, float, float, float]:
    """
    Run our Bellman-Ford implementation with timing
    
    Args:
        edges: List of tuples (u, v, weight) representing transactions
        num_vertices: Number of vertices in the graph
        
    Returns:
        has_cycle: Whether a negative cycle was detected
        cycle: The negative cycle (if any)
        profit: Profit factor of the cycle
        total_weight: Total weight of the cycle
        execution_time: Time taken in seconds
    """
    # Time our implementation
    start_time = time.time()
    
    # Run our Bellman-Ford
    _, pred, neg_cycle_start = bellman_ford(edges, num_vertices)
    
    has_cycle = False
    cycle = None
    profit = 1.0
    total_weight = 0.0
    
    if neg_cycle_start is not None:
        cycle, profit, total_weight, _ = extract_cycle(pred, neg_cycle_start, edges, num_vertices)
        has_cycle = len(cycle) > 1 and profit > 1.0
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return has_cycle, cycle, profit, total_weight, execution_time


def run_single_benchmark(dataset_id: int, num_currencies: int, num_transactions: int, insert_cycle: bool = True) -> Dict:
    """
    Run a single benchmark comparison
    
    Args:
        dataset_id: Identifier for this benchmark run
        num_currencies: Number of currencies in the dataset
        num_transactions: Number of transactions in the dataset
        insert_cycle: Whether to insert a known negative cycle
        
    Returns:
        Dictionary containing benchmark results
    """
    # Create dataset
    edges, num_currencies = create_random_dataset(num_currencies, num_transactions, insert_cycle)
    
    # Run NetworkX benchmark
    nx_has_cycle, nx_cycle, nx_cycle_weight, nx_profit_factor, nx_time = run_networkx_benchmark(edges, num_currencies)
    
    # Run our implementation benchmark
    our_has_cycle, our_cycle, our_profit, our_total_weight, our_time = run_our_implementation_benchmark(edges, num_currencies)
    
    # Calculate speedup
    speedup = nx_time / our_time if our_time > 0 else float('inf')
    
    # Check agreement
    cycles_agree = (nx_has_cycle and our_has_cycle) or (not nx_has_cycle and not our_has_cycle)
    
    return {
        'dataset_id': dataset_id,
        'num_currencies': num_currencies,
        'num_transactions': num_transactions,
        'insert_cycle': insert_cycle,
        'nx_has_cycle': nx_has_cycle,
        'nx_time': nx_time,
        'nx_profit_factor': nx_profit_factor,
        'our_has_cycle': our_has_cycle,
        'our_time': our_time,
        'our_profit': our_profit,
        'speedup': speedup,
        'cycles_agree': cycles_agree
    }


def format_time(time_seconds: float) -> str:
    """Format time with appropriate units"""
    if time_seconds < 0.001:
        return f"{time_seconds*1000000:.2f} μs"
    elif time_seconds < 1:
        return f"{time_seconds*1000:.2f} ms"
    else:
        return f"{time_seconds:.4f} s"


def create_benchmark_table(results: List[Dict]) -> Table:
    """Create a rich table for benchmark results"""
    table = Table(title="Bellman-Ford Implementation Benchmark Results")
    
    table.add_column("Dataset", style="cyan", no_wrap=True)
    table.add_column("Currencies", style="magenta")
    table.add_column("Edges", style="magenta")
    table.add_column("NetworkX Time", style="green")
    table.add_column("Our Time", style="green")
    table.add_column("Speedup", style="yellow")
    table.add_column("NX Cycle", style="red")
    table.add_column("Our Cycle", style="red")
    table.add_column("Agree", style="blue")
    
    for result in results:
        table.add_row(
            f"#{result['dataset_id']}",
            str(result['num_currencies']),
            str(result['num_transactions']),
            format_time(result['nx_time']),
            format_time(result['our_time']),
            f"{result['speedup']:.2f}x" if result['speedup'] != float('inf') else "∞",
            "✓" if result['nx_has_cycle'] else "✗",
            "✓" if result['our_has_cycle'] else "✗",
            "✓" if result['cycles_agree'] else "✗"
        )
    
    return table


def create_summary_table(results: List[Dict]) -> Table:
    """Create a summary table with statistics"""
    table = Table(title="Benchmark Summary Statistics")
    
    # Extract timing data
    nx_times = [r['nx_time'] for r in results]
    our_times = [r['our_time'] for r in results]
    speedups = [r['speedup'] for r in results if r['speedup'] != float('inf')]
    
    # Calculate statistics
    nx_mean = statistics.mean(nx_times)
    nx_median = statistics.median(nx_times)
    nx_min = min(nx_times)
    nx_max = max(nx_times)
    
    our_mean = statistics.mean(our_times)
    our_median = statistics.median(our_times)
    our_min = min(our_times)
    our_max = max(our_times)
    
    speedup_mean = statistics.mean(speedups) if speedups else 0
    speedup_median = statistics.median(speedups) if speedups else 0
    
    # Agreement statistics
    agreements = sum(1 for r in results if r['cycles_agree'])
    agreement_rate = agreements / len(results) * 100
    
    # Cycle detection statistics
    nx_cycles = sum(1 for r in results if r['nx_has_cycle'])
    our_cycles = sum(1 for r in results if r['our_has_cycle'])
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("NetworkX", style="green")
    table.add_column("Our Implementation", style="green")
    table.add_column("Speedup", style="yellow")
    
    table.add_row("Mean Time", format_time(nx_mean), format_time(our_mean), f"{speedup_mean:.2f}x")
    table.add_row("Median Time", format_time(nx_median), format_time(our_median), f"{speedup_median:.2f}x")
    table.add_row("Min Time", format_time(nx_min), format_time(our_min), "-")
    table.add_row("Max Time", format_time(nx_max), format_time(our_max), "-")
    table.add_row("Cycles Detected", str(nx_cycles), str(our_cycles), "-")
    table.add_row("Agreement Rate", f"{agreement_rate:.1f}%", f"{agreement_rate:.1f}%", "-")
    
    return table


def main(
    num_datasets: int = typer.Option(10, "--datasets", "-d", help="Number of datasets to benchmark"),
    num_currencies: int = typer.Option(100, "--currencies", "-c", help="Number of currencies per dataset"),
    num_transactions: int = typer.Option(1000, "--transactions", "-t", help="Number of transactions per dataset"),
    insert_cycle: bool = typer.Option(True, "--insert-cycle/--no-insert-cycle", help="Whether to insert a known negative cycle"),
):
    """Main benchmarking function"""
    console.print("\n" + "=" * 80, style="bold blue")
    console.print(f"{'BELLMAN-FORD IMPLEMENTATION BENCHMARK':^80}", style="bold blue")
    console.print("=" * 80, style="bold blue")
    
    console.print(f"\nRunning benchmark on {num_datasets} random datasets:")
    console.print(f"  • Currencies per dataset: {num_currencies}")
    console.print(f"  • Transactions per dataset: {num_transactions}")
    console.print(f"  • Insert known cycle: {insert_cycle}")
    console.print()
    
    # Run benchmarks
    results = []
    for i in track(range(num_datasets), description="Running benchmarks..."):
        result = run_single_benchmark(i + 1, num_currencies, num_transactions, insert_cycle)
        results.append(result)
    
    # Display results
    console.print("\n" + "=" * 80, style="bold green")
    console.print("DETAILED RESULTS", style="bold green")
    console.print("=" * 80, style="bold green")
    
    benchmark_table = create_benchmark_table(results)
    console.print(benchmark_table)
    
    console.print("\n" + "=" * 80, style="bold green")
    console.print("SUMMARY STATISTICS", style="bold green")
    console.print("=" * 80, style="bold green")
    
    summary_table = create_summary_table(results)
    console.print(summary_table)
    
    # Performance analysis
    console.print("\n" + "=" * 80, style="bold yellow")
    console.print("PERFORMANCE ANALYSIS", style="bold yellow")
    console.print("=" * 80, style="bold yellow")
    
    # Calculate overall statistics
    nx_times = [r['nx_time'] for r in results]
    our_times = [r['our_time'] for r in results]
    speedups = [r['speedup'] for r in results if r['speedup'] != float('inf')]
    
    if speedups:
        avg_speedup = statistics.mean(speedups)
        if avg_speedup > 1:
            console.print(f"✓ Our implementation is on average {avg_speedup:.2f}x faster than NetworkX", style="bold green")
        else:
            console.print(f"⚠ Our implementation is on average {1/avg_speedup:.2f}x slower than NetworkX", style="bold yellow")
    else:
        console.print("⚠ Unable to calculate average speedup", style="bold yellow")
    
    # Agreement analysis
    agreements = sum(1 for r in results if r['cycles_agree'])
    agreement_rate = agreements / len(results) * 100
    
    if agreement_rate == 100:
        console.print("✓ Perfect agreement on cycle detection between implementations", style="bold green")
    elif agreement_rate >= 90:
        console.print(f"✓ Good agreement on cycle detection ({agreement_rate:.1f}%)", style="bold green")
    elif agreement_rate >= 70:
        console.print(f"⚠ Moderate agreement on cycle detection ({agreement_rate:.1f}%)", style="bold yellow")
    else:
        console.print(f"✗ Poor agreement on cycle detection ({agreement_rate:.1f}%)", style="bold red")
    
    # Cycle detection analysis
    nx_cycles = sum(1 for r in results if r['nx_has_cycle'])
    our_cycles = sum(1 for r in results if r['our_has_cycle'])
    
    console.print(f"\nCycle Detection Summary:")
    console.print(f"  • NetworkX detected cycles in {nx_cycles}/{num_datasets} datasets")
    console.print(f"  • Our implementation detected cycles in {our_cycles}/{num_datasets} datasets")
    
    if nx_cycles == our_cycles:
        console.print("  ✓ Both implementations detected the same number of cycles", style="bold green")
    else:
        console.print("  ⚠ Different number of cycles detected between implementations", style="bold yellow")


if __name__ == "__main__":
    typer.run(main) 