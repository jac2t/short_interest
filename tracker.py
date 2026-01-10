import yfinance as yf
import pandas as pd
import requests
import concurrent.futures
import time
import os

def get_sp500_tickers():
    """Scrapes the list of S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = pd.read_html(response.text)
        # The first table usually contains the constituents
        df = tables[0]
        tickers = df['Symbol'].tolist()
        # Clean tickers (e.g., BRK.B -> BRK-B for yfinance)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_short_data(ticker):
    """Fetches short interest data for a single ticker."""
    try:
        # Use yfinance Ticker object
        stock = yf.Ticker(ticker)
        # info dictionary contains the data we need
        info = stock.info
        
        # Extract relevant fields, defaulting to 0 or None if missing
        short_percent = info.get('shortPercentOfFloat', 0)
        shares_short = info.get('sharesShort', 0)
        current_price = info.get('currentPrice', 0)
        
        if short_percent is None: short_percent = 0
        if shares_short is None: shares_short = 0
        if current_price is None: current_price = 0

        # Calculate absolute dollar value shorted
        dollar_short = shares_short * current_price

        return {
            'Ticker': ticker,
            'Name': info.get('shortName', ticker),
            'Short % of Float': short_percent,
            'Shares Short': shares_short,
            'Current Price': current_price,
            'Dollar Value Shorted': dollar_short
        }
    except Exception as e:
        # print(f"Error fetching data for {ticker}: {e}") # Optional: silence errors specifically for clean output
        return None

def main():
    print("Starting S&P 500 Short Interest Tracker...")
    
    tickers = get_sp500_tickers()
    if not tickers:
        print("No tickers found. Exiting.")
        return

    print(f"Found {len(tickers)} tickers. Fetching data...")
    
    results = []
    # Use ThreadPoolExecutor for concurrent API calls
    # Adjust max_workers based on API limits/system capabilities. 20 is usually a safe bet for IO bound.
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(get_short_data, ticker): ticker for ticker in tickers}
        
        count = 0
        total = len(tickers)
        for future in concurrent.futures.as_completed(future_to_ticker):
            data = future.result()
            if data:
                results.append(data)
            count += 1
            if count % 50 == 0:
                print(f"Processed {count}/{total} tickers...")

    if not results:
        print("No data collected.")
        return

    df = pd.DataFrame(results)

    # --- Processing for Top 10 Lists ---
    
    # 1. Top 10 by % Float Shorted
    # Convert decimal to percentage for display if needed, but keeping raw for sorting is better first.
    top_percent = df.sort_values(by='Short % of Float', ascending=False).head(10).copy()
    
    # Format for display
    top_percent_display = top_percent[['Ticker', 'Name', 'Short % of Float', 'Dollar Value Shorted', 'Current Price']].copy()
    top_percent_display['Short % of Float'] = top_percent_display['Short % of Float'].apply(lambda x: f"{x:.2%}")
    top_percent_display['Dollar Value Shorted'] = top_percent_display['Dollar Value Shorted'].apply(lambda x: f"${x:,.0f}")
    top_percent_display['Current Price'] = top_percent_display['Current Price'].apply(lambda x: f"${x:.2f}")

    # 2. Top 10 by Absolute Dollar Value
    top_dollar = df.sort_values(by='Dollar Value Shorted', ascending=False).head(10).copy()
    
    # Format for display
    top_dollar_display = top_dollar[['Ticker', 'Name', 'Dollar Value Shorted', 'Short % of Float', 'Current Price']].copy()
    top_dollar_display['Dollar Value Shorted'] = top_dollar_display['Dollar Value Shorted'].apply(lambda x: f"${x:,.0f}")
    top_dollar_display['Short % of Float'] = top_dollar_display['Short % of Float'].apply(lambda x: f"{x:.2%}")
    top_dollar_display['Current Price'] = top_dollar_display['Current Price'].apply(lambda x: f"${x:.2f}")


    # --- Save Snapshot ---
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    json_path = os.path.join(data_dir, f"{today}.json")
    
    # Save full dataset or just the top lists? 
    # Plan said "Save weekly scans... [{ticker, short_float...}]"
    # It's better to save the full list (or at least top 50/100) so we have raw data.
    # Let's save the full list for now, it's not that big for 500 items.
    
    # Convert dataframe to list of dicts
    json_data = df.to_dict(orient='records')
    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"Saved snapshot to {json_path}")
    
    # --- Update Index ---
    # List all json files in data_dir to create an index for the frontend
    files = sorted([f for f in os.listdir(data_dir) if f.endswith(".json") and f != "index.json"], reverse=True)
    index_path = os.path.join(data_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(files, f, indent=2)
    print(f"Updated index at {index_path}")

    # --- Generate Markdown ---
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S EST") # Note: server time might not be EST, but we label it.
    
    md_content = f"# S&P 500 Short Interest Tracker\n\n"
    md_content += f"*Last Updated: {timestamp}*\n\n"
    
    md_content += "## Top 10 by % Float Shorted\n"
    md_content += top_percent_display.to_markdown(index=False)
    md_content += "\n\n"
    
    md_content += "## Top 10 by Absolute Dollar Value Shorted\n"
    md_content += top_dollar_display.to_markdown(index=False)
    md_content += "\n"

    # Write to README.md
    readme_path = "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Successfully updated {readme_path}")

if __name__ == "__main__":
    main()
