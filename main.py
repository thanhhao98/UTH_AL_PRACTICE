import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from dataset import create_dataset
from real_dataset import (
    create_real_dataset,
    format_currency_path,
    create_currency_results_table,
)
from bellman_ford import (
    bellman_ford,
    extract_cycle,
    format_cycle_path,
    create_results_table,
)
from validation import run_algorithms, validate_results

console = Console()


def format_networkx_cycle(cycle, currencies, currency_codes=None):
    """Format NetworkX cycle for display"""
    if not cycle or len(cycle) < 2:
        return "No cycle detected"

    if currency_codes:
        # Use real currency codes
        return " → ".join(
            [
                currency_codes[c] if c < len(currency_codes) else f"Currency {c}"
                for c in cycle
            ]
        )
    else:
        # Use generic currency names
        return " → ".join([f"Currency {c}" for c in cycle])


def run_arbitrage_detection(
    num_currencies: int = 500,
    num_transactions: int = 100000,
    insert_cycle: bool = True,
    use_real_data: bool = False,
    use_historical: bool = False,
):
    """
    Run arbitrage detection with the specified parameters

    Args:
        num_currencies: Number of currency nodes
        num_transactions: Number of directed edges (transactions)
        insert_cycle: Whether to insert a known negative cycle
        use_real_data: Whether to use real exchange rate data
        use_historical: If using real data, whether to use historical rates
    """
    console.print("\n" + "=" * 80, style="bold blue")
    console.print(f"{'ARBITRAGE DETECTION USING BELLMAN-FORD':^80}", style="bold blue")
    console.print("=" * 80, style="bold blue")

    # Generate dataset - either synthetic or real
    currency_codes = None
    if use_real_data:
        console.print(
            "Using [bold]real exchange rate data[/bold] from European Central Bank",
            style="cyan",
        )
        edges, num_currencies, currency_codes = create_real_dataset(
            use_historical=use_historical, num_currencies=num_currencies
        )
        console.print(f"Analyzing market with {num_currencies} real currencies\n")
    else:
        console.print(
            f"Using [bold]synthetic data[/bold] with {num_currencies} currencies and {num_transactions} exchange rates\n"
        )
        edges, num_currencies = create_dataset(
            num_currencies, num_transactions, insert_cycle
        )

    console.print(
        f"Running Bellman-Ford algorithm to detect arbitrage opportunities...\n"
    )

    # Run Bellman-Ford
    dist, pred, neg_cycle_start = bellman_ford(edges, num_currencies)

    # Process results
    if neg_cycle_start is None:
        console.print(
            "✘ No negative cycle detected - No arbitrage opportunities found.",
            style="bold red",
        )
    else:
        cycle, profit, total_weight, cycle_rates = extract_cycle(
            pred, neg_cycle_start, edges, num_currencies
        )

        # Check if this is a valid cycle
        if len(cycle) <= 1:
            console.print("✘ No valid arbitrage cycle detected.", style="bold red")
            console.print(
                "  The algorithm found a potential cycle but it was filtered out as invalid.",
                style="dim",
            )
        else:
            # Check if this is a valid arbitrage (profit factor > 1)
            is_arbitrage = profit > 1

            if is_arbitrage:
                console.print("✓ ARBITRAGE OPPORTUNITY DETECTED!", style="bold green")
            else:
                console.print(
                    "⚠ Cycle detected but not profitable (no arbitrage)!",
                    style="bold yellow",
                )

            console.print("-" * 60)

            # Format cycle path
            if use_real_data and currency_codes:
                formatted_path = format_currency_path(
                    cycle, cycle_rates, currency_codes
                )
                table = create_currency_results_table(
                    cycle, cycle_rates, currency_codes, total_weight, profit
                )
            else:
                formatted_path = format_cycle_path(cycle, cycle_rates)
                table = create_results_table(cycle, cycle_rates, total_weight, profit)

            console.print(f"Cycle: {formatted_path}")

            # Print detailed path with exchange rates
            console.print(table)

            console.print("-" * 60)
            console.print(f"Total cycle weight:  {total_weight:.6f}")

            profit_style = "bold green" if profit > 1 else "bold red"
            profit_sign = "+" if profit > 1 else ""
            console.print(
                f"Profit factor:       {profit:.6f} [{profit_style}]({profit_sign}{(profit-1)*100:.2f}% profit per full cycle)[/{profit_style}]"
            )

            # Calculate profit from example starting amount
            start_amount = 1000
            end_amount = start_amount * profit
            profit_amount = end_amount - start_amount
            profit_style = "green" if profit_amount > 0 else "red"
            console.print(
                f"(Profit: {profit_sign}{profit_amount:.2f})", style=profit_style
            )

    console.print("\n" + "-" * 80, style="blue")
    console.print("VALIDATION RESULTS", style="blue bold")
    console.print("-" * 80, style="blue")

    # Run algorithms
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
    ) = run_algorithms(edges, num_currencies)

    # Validate results
    is_valid, cycles_agree = validate_results(
        nx_has_cycle, our_has_cycle, our_has_arbitrage
    )

    validation_style = "green" if is_valid else "red"
    console.print(
        f"✓ NetworkX validation: {'Passed' if is_valid else 'Failed'}",
        style=validation_style,
    )

    # Display performance comparison
    console.print("\n[bold]PERFORMANCE COMPARISON:[/bold]")
    console.print("-" * 40)
    
    # Format timing with appropriate precision
    if nx_time < 0.001:
        nx_time_str = f"{nx_time*1000000:.2f} μs"
    elif nx_time < 1:
        nx_time_str = f"{nx_time*1000:.2f} ms"
    else:
        nx_time_str = f"{nx_time:.4f} s"
        
    if our_time < 0.001:
        our_time_str = f"{our_time*1000000:.2f} μs"
    elif our_time < 1:
        our_time_str = f"{our_time*1000:.2f} ms"
    else:
        our_time_str = f"{our_time:.4f} s"
    
    console.print(f"  NetworkX Bellman-Ford: {nx_time_str}")
    console.print(f"  Our Implementation:     {our_time_str}")
    
    # Calculate speedup/slowdown
    if our_time > 0:
        speedup = nx_time / our_time
        if speedup > 1:
            console.print(f"  Speedup: Our implementation is {speedup:.2f}x faster", style="bold green")
        elif speedup < 1:
            slowdown = our_time / nx_time
            console.print(f"  Slowdown: Our implementation is {slowdown:.2f}x slower", style="bold yellow")
        else:
            console.print("  Performance: Both implementations are equally fast", style="bold blue")
    else:
        console.print("  Performance: Unable to calculate (our implementation took 0 time)", style="dim")

    # Show NetworkX cycle information with better formatting
    if nx_has_cycle:
        console.print("\n[bold]NetworkX Cycle Details:[/bold]")
        if nx_cycle:
            formatted_nx_cycle = format_networkx_cycle(
                nx_cycle, num_currencies, currency_codes if use_real_data else None
            )
            console.print(f"  Cycle: {formatted_nx_cycle}")

            # Display NetworkX cycle weight and profit factor
            profit_style = "bold green" if nx_profit_factor > 1 else "bold red"
            profit_sign = "+" if nx_profit_factor > 1 else ""
            console.print(f"  Cycle weight: {nx_cycle_weight:.6f}")
            console.print(
                f"  Profit factor: {nx_profit_factor:.6f} ({profit_sign}{(nx_profit_factor-1)*100:.2f}%)",
                style=profit_style,
            )
        else:
            console.print("  No specific cycle was extracted from NetworkX")

    console.print("\n[bold]Our Implementation Details:[/bold]")
    console.print(f"  • NetworkX detected negative cycle: {nx_has_cycle}")

    if our_cycle:
        console.print(f"  • Our implementation detected cycle: {our_has_cycle}")
        console.print(f"  • Our cycle is profitable (arbitrage): {our_has_arbitrage}")
    else:
        console.print(f"  • Our implementation detected cycle: False")

    console.print(f"  • Agreement on cycle detection: {cycles_agree}")

    if cycles_agree:
        console.print(
            "\n✓ The cycle validation is successful! Both implementations agree.",
            style="bold green",
        )
    else:
        console.print(
            "\n⚠ Implementations interpret cycle differently.", style="bold yellow"
        )
        console.print(
            "  This can happen due to different algorithms or edge case handling.",
            style="dim",
        )


def main():
    typer.run(run_arbitrage_detection)


if __name__ == "__main__":
    main()
