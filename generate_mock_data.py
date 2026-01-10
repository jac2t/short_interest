import os
import json
import random
import datetime
import pandas as pd

# Reuse ticker logic or just hardcode a few for the mock? 
# Better to be realistic. Let's make a simple list of popular tickers.
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "AMD", "NFLX", "GME", "AMC", "SPY", "QQQ", "IWM", "V", "JPM", "DIS", "BA", "INTC", "CSCO"]

def generate_mock_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Start from Jan 5, 2024 (First Friday)
    start_date = datetime.date(2024, 1, 5)
    end_date = datetime.date.today()
    
    current_date = start_date
    while current_date <= end_date:
        print(f"Generating data for {current_date}...")
        
        # Simulate some data for this week
        weekly_data = []
        for ticker in TICKERS:
            # Randomize stats slightly
            current_price = random.uniform(50, 500)
            shares_short = random.randint(1000000, 50000000)
            short_percent = random.uniform(0.005, 0.25) # 0.5% to 25%
            
            dollar_short = shares_short * current_price
            
            weekly_data.append({
                'Ticker': ticker,
                'Name': f"{ticker} Corp", # Placeholder name
                'Short % of Float': short_percent,
                'Shares Short': shares_short,
                'Current Price': current_price,
                'Dollar Value Shorted': dollar_short
            })
            
        # Save JSON
        filename = f"{current_date.strftime('%Y-%m-%d')}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(weekly_data, f, indent=2)
            
        # Move to next Friday
        current_date += datetime.timedelta(days=7)

if __name__ == "__main__":
    generate_mock_data()
