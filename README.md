# Currency Arbitrage Detection

A Python implementation of the Bellman-Ford algorithm to detect currency arbitrage opportunities in exchange rate networks.

## Overview

This program simulates a currency exchange network and uses the Bellman-Ford algorithm to detect negative cycles, which represent arbitrage opportunities in currency markets. An arbitrage opportunity exists when a sequence of currency exchanges leads back to the original currency with more money than the starting amount.

The implementation:
- Creates a synthetic dataset of currency exchange rates
- Can use real exchange rate data from the European Central Bank
- Applies the Bellman-Ford algorithm to detect negative cycles
- Validates the implementation against NetworkX library
- Provides detailed output of detected arbitrage opportunities

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the program with default settings:
```bash
python main.py
```

### Command-line Options

- `--num-currencies`: Number of currency nodes (default: 500)
- `--num-transactions`: Number of directed edges/transactions (default: 100000)
- `--insert-cycle/--no-insert-cycle`: Whether to insert a known negative cycle (default: insert-cycle)
- `--max-iterations`: Maximum number of Bellman-Ford iterations (default: num_currencies, capped at 1000)
- `--use-real-data/--no-use-real-data`: Whether to use real exchange rate data (default: no-use-real-data)
- `--use-historical/--no-use-historical`: With real data, whether to use historical rates (default: no-use-historical)

Examples:
```bash
# Run with 100 currencies and 5000 transactions
python main.py --num-currencies 100 --num-transactions 5000

# Run without inserting a known negative cycle
python main.py --no-insert-cycle

# Run with a maximum of 50 iterations (for large datasets)
python main.py --max-iterations 50

# Run with real exchange rate data from the European Central Bank
python main.py --use-real-data

# Run with historical exchange rate data (past 90 days)
python main.py --use-real-data --use-historical --num-currencies 30

# Show all available options
python main.py --help
```

## Data Sources

### Synthetic Data

By default, the program generates synthetic exchange rates between random currencies. This is useful for testing and exploring the algorithm's behavior.

### Real Exchange Rate Data

The program can fetch real exchange rate data from the European Central Bank (ECB):

- **Daily Rates**: The most recent exchange rates for major currencies with EUR as the base
- **Historical Rates**: Exchange rates for the past 90 days, allowing for more thorough analysis

When using real exchange rate data, the program:
1. Fetches data from the ECB's XML feeds 
2. Caches the data locally to avoid repeated downloads
3. Creates a fully connected graph with all possible currency pairs
4. Displays actual currency codes in the output

## Performance Safeguards

The implementation includes several safeguards to prevent infinite loops and ensure reasonable performance:

1. **Maximum Iteration Limit**: The Bellman-Ford algorithm is capped at a maximum number of iterations (controlled by `--max-iterations`), preventing excessive runtime for large graphs.

2. **Early Termination**: The algorithm stops early if no edge relaxations occur in an iteration, significantly speeding up execution for well-behaved graphs.

3. **Edge Validation**: Guards against invalid vertex indices, preventing potential crashes or undefined behavior.

4. **Large Graph Handling**: For very large graphs (over 10,000 edges), the algorithm samples a subset of edges when checking for negative cycles, maintaining reasonable performance.

5. **Infinite Value Handling**: Special handling for infinite distance values prevents numeric errors during relaxation.

These safeguards make the algorithm robust for both small test cases and large real-world datasets.

## Testing

The project includes a comprehensive test script (`test.py`) that runs multiple combinations of parameters to validate the algorithm's behavior across different scenarios.

### Running Tests

Run the test suite with:
```bash
python test.py
```

The test script will:
1. Execute the algorithm with various combinations of currency counts, transaction counts, and with/without inserted cycles
2. Track successful runs and any failures
3. Generate a detailed report

### Test Results

The test results include:
- Summary statistics (total tests, success rate)
- Detailed table of all test cases and their outcomes
- Analysis of arbitrage detection patterns
- Details of any failures encountered

Sample output:
```
Test Suite Summary
Total tests run: 30
Success: 30
Failures: 0
Success rate: 100.0%

Test Results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Currencies ┃ Transactions ┃ Inserted Cycle ┃ Arbitrage ┃ Validation ┃ Agreement  ┃ Profit Factor ┃ Success ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ 2          │ 4            │ Yes           │ ✓         │ ✓          │ ✓          │ 2.15          │ Pass    │
│ 2          │ 4            │ No            │ ✓         │ ✓          │ ✓          │ 1.89          │ Pass    │
│ ...        │ ...          │ ...           │ ...       │ ...        │ ...        │ ...           │ ...     │
└────────────┴──────────────┴───────────────┴───────────┴────────────┴────────────┴───────────────┴─────────┘

Pattern Analysis
Tests with inserted cycle that found arbitrage: 15/15
Tests without inserted cycle that found arbitrage: 12/15
```

### Customizing Tests

You can modify the test parameters in `test.py` to focus on specific scenarios:

```python
# Define test parameters
currency_counts = [2, 5, 10, 20, 50, 100]
transaction_counts = [4, 10, 20, 50, 100, 500]
cycle_options = [True, False]
```

## Code Structure

The project is organized into several modules:

- **dataset.py**: Functions for generating synthetic currency exchange rate data
- **bellman_ford.py**: Implementation of the Bellman-Ford algorithm and cycle extraction
- **validation.py**: Functions to validate our implementation against NetworkX
- **main.py**: CLI interface and output formatting
- **test.py**: Automated testing with multiple parameter combinations

## How It Works

Currency exchange rates are represented as a directed graph where:
- Nodes represent currencies
- Edges represent exchange rates between currencies
- Edge weights are negative logarithms of exchange rates (w = -log(rate))

With this representation:
1. A cycle with negative total weight indicates an arbitrage opportunity
2. The profit factor is e^(-total_weight) 
3. A profit factor > 1 means there is a profitable arbitrage circuit

## Example Output

```
================================================================================
                     ARBITRAGE DETECTION USING BELLMAN-FORD                     
================================================================================
Analyzing market with 100 currencies and 5000 exchange rates

Running Bellman-Ford algorithm to detect arbitrage opportunities...

✓ ARBITRAGE OPPORTUNITY DETECTED!
------------------------------------------------------------
Cycle: Currency 20 → Currency 30 → Currency 40 → Currency 10 → Currency 20
           Detailed Exchange Path            
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃        From ┃          To ┃ Exchange Rate ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Currency 20 │ Currency 30 │      1.941099 │
│ Currency 30 │ Currency 40 │      1.020000 │
│ Currency 40 │ Currency 10 │      1.030000 │
│ Currency 10 │ Currency 20 │      0.837747 │
└─────────────┴─────────────┴───────────────┘
------------------------------------------------------------
Total cycle weight:  -0.535576
Profit factor:       1.708433 (+70.84% profit per full cycle)

Example: 1000 units → 1708.43 units  (Profit: +708.43)
```

## References

- For more on the Bellman-Ford algorithm: [Wikipedia - Bellman-Ford Algorithm](https://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm)
- For more on currency arbitrage: [Investopedia - Currency Arbitrage](https://www.investopedia.com/terms/c/currency-arbitrage.asp)
