import typer
from typing import Optional
from rich.console import Console

from dataset import create_dataset
from real_dataset import create_real_dataset, format_currency_path, create_currency_results_table
from bellman_ford import bellman_ford, extract_cycle, format_cycle_path, create_results_table
from validation import validate_bellman_ford_with_library

console = Console()

def run_arbitrage_detection(
    num_currencies: int = 500,
    num_transactions: int = 100000,
    insert_cycle: bool = True,
    max_iterations: int = None,
    use_real_data: bool = False,
    use_historical: bool = False,
):
    """
    Run arbitrage detection with the specified parameters
    
    Args:
        num_currencies: Number of currency nodes
        num_transactions: Number of directed edges (transactions)
        insert_cycle: Whether to insert a known negative cycle
        max_iterations: Maximum iterations for Bellman-Ford (limits runtime)
        use_real_data: Whether to use real exchange rate data
        use_historical: If using real data, whether to use historical rates
    """
    console.print("\n" + "="*80, style="bold blue")
    console.print(f"{'ARBITRAGE DETECTION USING BELLMAN-FORD':^80}", style="bold blue")
    console.print("="*80, style="bold blue")
    
    # Generate dataset - either synthetic or real
    currency_codes = None
    if use_real_data:
        console.print("Using [bold]real exchange rate data[/bold] from European Central Bank", style="cyan")
        edges, num_currencies, currency_codes = create_real_dataset(
            use_historical=use_historical, 
            num_currencies=num_currencies
        )
        console.print(f"Analyzing market with {num_currencies} real currencies\n")
    else:
        console.print(f"Using [bold]synthetic data[/bold] with {num_currencies} currencies and {num_transactions} exchange rates\n")
        edges, num_currencies = create_dataset(num_currencies, num_transactions, insert_cycle)
    
    console.print(f"Running Bellman-Ford algorithm to detect arbitrage opportunities...\n")
    
    # Run Bellman-Ford with max_iterations limit
    dist, pred, neg_cycle_start = bellman_ford(edges, num_currencies, max_iterations)
    
    # Process results
    if neg_cycle_start is None:
        console.print("✘ No negative cycle detected - No arbitrage opportunities found.", style="bold red")
    else:
        cycle, profit, total_weight, cycle_rates = extract_cycle(pred, neg_cycle_start, edges, num_currencies)
        
        # Check if this is a valid cycle
        if len(cycle) <= 1:
            console.print("✘ No valid arbitrage cycle detected.", style="bold red")
            console.print("  The algorithm found a potential cycle but it was filtered out as invalid.", style="dim")
        else:        
            # Check if this is a valid arbitrage (profit factor > 1)
            is_arbitrage = profit > 1
            
            if is_arbitrage:
                console.print("✓ ARBITRAGE OPPORTUNITY DETECTED!", style="bold green")
            else:
                console.print("⚠ Cycle detected but not profitable (no arbitrage)!", style="bold yellow")
                
            console.print("-" * 60)
            
            # Format cycle path
            if use_real_data and currency_codes:
                formatted_path = format_currency_path(cycle, cycle_rates, currency_codes)
                table = create_currency_results_table(cycle, cycle_rates, currency_codes, total_weight, profit)
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
            console.print(f"Profit factor:       {profit:.6f} [{profit_style}]({profit_sign}{(profit-1)*100:.2f}% profit per full cycle)[/{profit_style}]")
            
            # Calculate how much profit from example starting amount
            start_amount = 1000
            end_amount = start_amount * profit
            profit_amount = end_amount - start_amount
            profit_style = "green" if profit_amount > 0 else "red"
            console.print(f"\nExample: {start_amount} units → {end_amount:.2f} units  ", end="")
            console.print(f"(Profit: {profit_sign}{profit_amount:.2f})", style=profit_style)
    
    console.print("\n" + "-"*80, style="blue")
    console.print("VALIDATION RESULTS", style="blue bold")
    console.print("-"*80, style="blue")
    
    # Validate with library
    is_valid, nx_has_cycle, our_cycle, our_has_arbitrage, cycles_agree = validate_bellman_ford_with_library(
        edges, num_currencies, max_iterations
    )
    
    validation_style = "green" if is_valid else "red"
    console.print(f"✓ NetworkX validation: {'Passed' if is_valid else 'Failed'}", style=validation_style)
    console.print(f"  • NetworkX detected negative cycle: {nx_has_cycle}")
    
    if our_cycle:
        console.print(f"  • Our implementation detected cycle: True")
        console.print(f"  • Our cycle is profitable (arbitrage): {our_has_arbitrage}")
    else:
        console.print(f"  • Our implementation detected cycle: False")
    
    console.print(f"  • Agreement on cycle detection: {cycles_agree}")
    
    if cycles_agree:
        console.print("\n✓ The cycle validation is successful! Both implementations agree.", style="bold green")
    else:
        console.print("\n⚠ Implementations interpret cycle differently.", style="bold yellow")
        console.print("  This can happen due to different algorithms or edge case handling.", style="dim")

def main():
    typer.run(run_arbitrage_detection)

if __name__ == "__main__":
    main()
