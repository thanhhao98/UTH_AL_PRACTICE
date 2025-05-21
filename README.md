# Currency Arbitrage Detection

A Python implementation of the Bellman-Ford algorithm to detect currency arbitrage opportunities in exchange rate networks.

## Overview

This program simulates a currency exchange network and uses the Bellman-Ford algorithm to detect negative cycles, which represent arbitrage opportunities in currency markets. An arbitrage opportunity exists when a sequence of currency exchanges leads back to the original currency with more money than the starting amount.

The implementation:
- Creates a synthetic dataset of currency exchange rates
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

Examples:
```bash
# Run with 100 currencies and 5000 transactions
python main.py --num-currencies 100 --num-transactions 5000

# Run without inserting a known negative cycle
python main.py --no-insert-cycle

# Show all available options
python main.py --help
```

## Code Structure

The project is organized into several modules:

- **dataset.py**: Functions for generating synthetic currency exchange rate data
- **bellman_ford.py**: Implementation of the Bellman-Ford algorithm and cycle extraction
- **validation.py**: Functions to validate our implementation against NetworkX
- **main.py**: CLI interface and output formatting

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