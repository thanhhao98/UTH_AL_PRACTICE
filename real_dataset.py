import math
import requests
import pandas as pd
import datetime
import os
from rich.console import Console

console = Console()

# URLs for data sources
ECB_DAILY_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_HIST_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"

# Local cache directory
CACHE_DIR = "data_cache"

def fetch_ecb_daily_rates():
    """Fetch latest daily exchange rates from European Central Bank"""
    try:
        console.print("Fetching daily exchange rates from ECB...", style="cyan")
        response = requests.get(ECB_DAILY_RATES_URL)
        response.raise_for_status()
        
        # Define namespaces used in ECB XML
        namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01', 
                     'eurofxref': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        
        df = pd.read_xml(response.content, xpath='.//eurofxref:Cube[@time]', namespaces=namespaces)
        
        date_str = df.iloc[0]['time'] if not df.empty else "latest"
        console.print(f"Using exchange rates from {date_str}", style="green")
        
        rates_df = pd.read_xml(response.content, xpath='.//eurofxref:Cube[@currency]', namespaces=namespaces)
        return rates_df
    except Exception as e:
        console.print(f"Error fetching ECB data: {e}", style="bold red")
        return None

def fetch_ecb_historical_rates(days=90):
    """Fetch historical exchange rates from European Central Bank"""
    try:
        console.print(f"Fetching historical exchange rates (past {days} days) from ECB...", style="cyan")
        response = requests.get(ECB_HIST_RATES_URL)
        response.raise_for_status()
        
        # Define namespaces used in ECB XML
        namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01', 
                     'eurofxref': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        
        rates_df = pd.read_xml(response.content, xpath='.//eurofxref:Cube[@currency]', namespaces=namespaces)
        
        dates = pd.read_xml(response.content, xpath='.//eurofxref:Cube[@time]', namespaces=namespaces)
        console.print(f"Retrieved exchange rates for {len(dates)} dates", style="green")
        
        return rates_df
    except Exception as e:
        console.print(f"Error fetching ECB historical data: {e}", style="bold red")
        return None

def create_real_dataset(use_historical=False, base_currency="EUR", num_currencies=None):
    """
    Create a dataset from real exchange rate data
    
    Args:
        use_historical: Whether to use historical data (True) or just the latest data (False)
        base_currency: The base currency (all rates are relative to this)
        num_currencies: Limit to this many currencies (or None for all available)
        
    Returns:
        edges: List of tuples (u, v, weight) representing exchange rates
        currency_codes: List of currency codes
    """
    # Ensure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Check for cached data
    cache_file = os.path.join(CACHE_DIR, "ecb_rates.csv")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cache_exists = os.path.exists(cache_file)
    
    rates_df = None
    
    # Use cached data if available and recent
    if cache_exists:
        rates_df = pd.read_csv(cache_file)
        if 'date' in rates_df.columns and today in rates_df['date'].values:
            console.print("Using cached exchange rate data", style="green")
        else:
            rates_df = None
    
    # Fetch new data if needed
    if rates_df is None:
        if use_historical:
            rates_df = fetch_ecb_historical_rates()
        else:
            rates_df = fetch_ecb_daily_rates()
        
        if rates_df is not None:
            rates_df.to_csv(cache_file, index=False)
    
    if rates_df is None or len(rates_df) == 0:
        console.print("Failed to retrieve exchange rate data. Using a small sample dataset.", style="bold yellow")
        # Use a small fallback dataset with major currencies
        rates_df = pd.DataFrame({
            'currency': ['USD', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'CNY'],
            'rate': [1.09, 164.7, 0.85, 0.97, 1.47, 1.65, 7.93],
            'date': [today] * 7
        })
    
    # Process the data into our graph format
    currency_codes = ['EUR']  # Base currency is always first
    currency_codes.extend(rates_df['currency'].unique().tolist())
    
    if num_currencies is not None and num_currencies < len(currency_codes):
        currency_codes = currency_codes[:num_currencies]
    
    num_currencies_actual = len(currency_codes)
    console.print(f"Using {num_currencies_actual} currencies: {', '.join(currency_codes[:min(10, num_currencies_actual)])}{'...' if num_currencies_actual > 10 else ''}", style="cyan")
    
    # Create a mapping from currency code to index
    currency_to_index = {code: i for i, code in enumerate(currency_codes)}
    
    edges = []
    
    # Group by date for historical data
    if 'time' in rates_df.columns:
        dates = rates_df['time'].unique()
        daily_groups = rates_df.groupby('time')
    else:
        dates = [today]
        daily_groups = [(today, rates_df)]
    
    # Process each date's rates
    for date, group in daily_groups:
        # Add EUR (base currency) to the dataframe with rate 1.0
        eur_row = pd.DataFrame({'currency': ['EUR'], 'rate': [1.0]})
        day_rates = pd.concat([eur_row, group[['currency', 'rate']]])
        
        # Only include currencies in our list
        day_rates = day_rates[day_rates['currency'].isin(currency_codes)]
        
        # Create edges for all currency pairs
        for i, row1 in day_rates.iterrows():
            curr1 = row1['currency']
            if curr1 not in currency_to_index:
                continue
                
            for j, row2 in day_rates.iterrows():
                if i == j:
                    continue
                    
                curr2 = row2['currency']
                if curr2 not in currency_to_index:
                    continue
                
                # Calculate exchange rate and convert to graph weight
                rate = row2['rate'] / row1['rate']
                weight = -math.log(rate)
                edges.append((currency_to_index[curr1], currency_to_index[curr2], weight))
    
    console.print(f"Created {len(edges)} edges from real exchange rate data", style="green")
    
    return edges, num_currencies_actual, currency_codes

def format_currency_path(cycle, cycle_rates, currency_codes):
    """Format cycle as a string with actual currency codes and exchange rates"""
    if not cycle or len(cycle) < 2:
        return "No cycle"
        
    path_parts = []
    for i in range(len(cycle)-1):
        u, v = cycle[i], cycle[i+1]
        u_code = currency_codes[u] if u < len(currency_codes) else f"Currency {u}"
        v_code = currency_codes[v] if v < len(currency_codes) else f"Currency {v}"
        rate = cycle_rates.get((u, v), 0)
        path_parts.append(f"{u_code} → {v_code} (rate: {rate:.4f})")
    
    u0 = cycle[0]
    u0_code = currency_codes[u0] if u0 < len(currency_codes) else f"Currency {u0}"
    return " → ".join([f"{u0_code}"] + [currency_codes[c] if c < len(currency_codes) else f"Currency {c}" for c in cycle[1:-1]] + [u0_code])

def create_currency_results_table(cycle, cycle_rates, currency_codes, total_weight, profit):
    """Create a Rich table for detailed results with actual currency codes"""
    from rich.table import Table
    
    table = Table(title="Detailed Exchange Path")
    
    table.add_column("From", style="cyan", justify="right")
    table.add_column("To", style="cyan", justify="right")
    table.add_column("Exchange Rate", style="green", justify="right")
    
    for i in range(len(cycle)-1):
        u, v = cycle[i], cycle[i+1]
        u_code = currency_codes[u] if u < len(currency_codes) else f"Currency {u}"
        v_code = currency_codes[v] if v < len(currency_codes) else f"Currency {v}"
        rate = cycle_rates.get((u, v), 0)
        table.add_row(u_code, v_code, f"{rate:.6f}")
    
    return table

if __name__ == "__main__":
    # Test the function
    edges, num_currencies, currency_codes = create_real_dataset(use_historical=True)
    print(f"Generated {len(edges)} edges for {num_currencies} currencies")
    print(f"Currency codes: {currency_codes[:10]}{'...' if len(currency_codes) > 10 else ''}") 