#!/usr/bin/env python3
import subprocess
import re
import time
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
import itertools

console = Console()


def run_test(currencies, transactions, insert_cycle=True):
    """Run a single test with the given parameters"""
    cmd = [
        "python",
        "main.py",
        f"--num-currencies={currencies}",
        f"--num-transactions={transactions}",
    ]
    if not insert_cycle:
        cmd.append("--no-insert-cycle")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        # Extract results using regex
        arbitrage_detected = "ARBITRAGE OPPORTUNITY DETECTED" in output
        validation_passed = "NetworkX validation: Passed" in output
        agreement = (
            "The cycle validation is successful! Both implementations agree." in output
        )

        # Extract profit factor if arbitrage was detected
        profit_factor = None
        if arbitrage_detected:
            profit_match = re.search(r"Profit factor:\s+(\d+\.\d+)", output)
            if profit_match:
                profit_factor = float(profit_match.group(1))

        return {
            "currencies": currencies,
            "transactions": transactions,
            "insert_cycle": insert_cycle,
            "arbitrage_detected": arbitrage_detected,
            "validation_passed": validation_passed,
            "agreement": agreement,
            "profit_factor": profit_factor,
            "success": True,
            "error": None,
        }
    except subprocess.CalledProcessError as e:
        return {
            "currencies": currencies,
            "transactions": transactions,
            "insert_cycle": insert_cycle,
            "arbitrage_detected": False,
            "validation_passed": False,
            "agreement": False,
            "profit_factor": None,
            "success": False,
            "error": str(e),
            "output": e.stdout,
        }


def run_test_suite():
    """Run a comprehensive test suite with various parameter combinations"""
    # Define test parameters - use smaller ranges for faster testing
    currency_counts = [2, 5, 10, 50]
    transaction_counts = [4, 50, 500]
    cycle_options = [True, False]

    # Generate all combinations
    test_cases = list(
        itertools.product(currency_counts, transaction_counts, cycle_options)
    )

    # Results storage
    results = []
    success_count = 0
    failure_count = 0

    # Run the tests with a progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[green]Running tests...", total=len(test_cases))

        for currencies, transactions, insert_cycle in test_cases:
            test_desc = (
                f"Testing with {currencies} currencies, {transactions} transactions, "
                + f"{'with' if insert_cycle else 'without'} inserted cycle"
            )
            progress.update(task, description=f"[cyan]{test_desc}")

            result = run_test(currencies, transactions, insert_cycle)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failure_count += 1

            # Small delay to avoid overloading system
            time.sleep(0.1)
            progress.advance(task)

    return results, success_count, failure_count


def generate_report(results, success_count, failure_count):
    """Generate a report table from the test results"""
    total_tests = len(results)

    # Summary table
    console.print("\n[bold green]Test Suite Summary[/bold green]")
    console.print(f"Total tests run: {total_tests}")
    console.print(f"Success: [green]{success_count}[/green]")
    console.print(f"Failures: [red]{failure_count}[/red]")
    console.print(
        f"Success rate: [{'green' if success_count == total_tests else 'yellow'}]{success_count/total_tests*100:.1f}%[/]"
    )

    # Result details
    console.print("\n[bold green]Test Results[/bold green]")

    detail_table = Table(show_header=True, header_style="bold")
    detail_table.add_column("Currencies")
    detail_table.add_column("Transactions")
    detail_table.add_column("Inserted Cycle")
    detail_table.add_column("Arbitrage")
    detail_table.add_column("Validation")
    detail_table.add_column("Agreement")
    detail_table.add_column("Profit Factor")
    detail_table.add_column("Success")

    # Sort results by currencies and transactions
    sorted_results = sorted(results, key=lambda x: (x["currencies"], x["transactions"]))

    for result in sorted_results:
        detail_table.add_row(
            str(result["currencies"]),
            str(result["transactions"]),
            "Yes" if result["insert_cycle"] else "No",
            "✓" if result["arbitrage_detected"] else "✗",
            "✓" if result["validation_passed"] else "✗",
            "✓" if result["agreement"] else "✗",
            f"{result['profit_factor']:.2f}" if result["profit_factor"] else "N/A",
            "[green]Pass[/green]" if result["success"] else "[red]Fail[/red]",
        )

    console.print(detail_table)

    # Failure details
    if failure_count > 0:
        console.print("\n[bold red]Failure Details[/bold red]")
        for i, result in enumerate(results):
            if not result["success"]:
                console.print(f"\n[red]Failure {i+1}:[/red]")
                console.print(
                    f"Parameters: {result['currencies']} currencies, {result['transactions']} transactions, insert_cycle={result['insert_cycle']}"
                )
                console.print(f"Error: {result['error']}")
                if "output" in result:
                    console.print("Output:")
                    console.print(result["output"])

    # Pattern analysis
    arbitrage_counts = {"with_cycle": 0, "without_cycle": 0}
    for result in results:
        if result["success"] and result["arbitrage_detected"]:
            if result["insert_cycle"]:
                arbitrage_counts["with_cycle"] += 1
            else:
                arbitrage_counts["without_cycle"] += 1

    console.print("\n[bold green]Pattern Analysis[/bold green]")
    console.print(
        f"Tests with inserted cycle that found arbitrage: {arbitrage_counts['with_cycle']}/{len([r for r in results if r['insert_cycle']])}"
    )
    console.print(
        f"Tests without inserted cycle that found arbitrage: {arbitrage_counts['without_cycle']}/{len([r for r in results if not r['insert_cycle']])}"
    )


def main():
    console.print("[bold]Currency Arbitrage Detection Test Suite[/bold]")
    console.print(
        "This test suite will run the algorithm with various parameter combinations."
    )

    results, success_count, failure_count = run_test_suite()
    generate_report(results, success_count, failure_count)


if __name__ == "__main__":
    main()
