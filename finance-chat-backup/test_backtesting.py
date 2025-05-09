import pandas as pd
from datetime import datetime, timedelta
from backtesting import backtest_strategy
from data_fetch import fetch_historical_data, fetch_market_data
from technical_analysis import calculate_indicators

def test_backtesting():
    """
    Test the backtesting functionality to ensure it properly handles holidays and weekends.
    """
    # Test with a known date
    analysis_date = datetime(2025, 4, 25)  # This is a Friday
    
    print(f"Testing backtesting with analysis date: {analysis_date}")
    
    # Fetch data for a common stock
    symbol = "AAPL"
    
    # Fetch historical data
    historical_data = fetch_historical_data(symbol, analysis_date - timedelta(days=60), analysis_date + timedelta(days=14))
    
    if historical_data is None or historical_data.empty:
        print(f"Error: Could not fetch historical data for {symbol}")
        return False
        
    print(f"Fetched {len(historical_data)} data points for {symbol}")
    
    # Calculate technical indicators
    historical_data = calculate_indicators(historical_data)
    
    if historical_data is None:
        print(f"Error: Could not calculate indicators for {symbol}")
        return False
        
    # Check if SMA_20 column exists (the function now adds columns to the DataFrame)
    if 'SMA_20' not in historical_data.columns:
        print(f"Error: SMA_20 column not found in historical data")
        print(f"Available columns: {historical_data.columns.tolist()}")
        return False
        
    print(f"Technical indicators calculated successfully")
    print(f"Available indicators: {list(historical_data.columns)}")
    
    # Run backtesting
    print(f"Running backtesting for {symbol} with analysis date: {analysis_date}")
    backtest_results = backtest_strategy(historical_data, analysis_date)
    
    if backtest_results is None:
        print(f"Error: Backtesting failed for {symbol}")
        return False
        
    # Print backtest results
    print(f"Entry date: {backtest_results['entry_date']}")
    print(f"Entry price: ${backtest_results['entry_price']:.2f}")
    
    if backtest_results['day3_date']:
        print(f"3-day date: {backtest_results['day3_date']}")
        print(f"3-day price: ${backtest_results['day3_price']:.2f}")
        print(f"3-day return: {backtest_results['day3_return']:.2f}%")
    else:
        print("No 3-day return data available")
        
    if backtest_results['day5_date']:
        print(f"5-day date: {backtest_results['day5_date']}")
        print(f"5-day price: ${backtest_results['day5_price']:.2f}")
        print(f"5-day return: {backtest_results['day5_return']:.2f}%")
    else:
        print("No 5-day return data available")
        
    # Test the market data fetching
    print("\nTesting market data fetching")
    market_data = fetch_market_data(analysis_date)
    
    if market_data is None or market_data.empty:
        print("Error: Could not fetch market data")
        return False
        
    print(f"Fetched {len(market_data)} market data points")
    
    # Check if required columns exist
    required_columns = ['Open', 'Close', 'High', 'Low']
    missing_columns = [col for col in required_columns if col not in market_data.columns]
    if missing_columns:
        print(f"Market data missing required columns: {missing_columns}")
        return False
        
    print("Market data fetching successful")
    
    # Calculate market indicators
    market_data = calculate_indicators(market_data)
    
    if market_data is None:
        print("Error: Could not calculate market indicators")
        return False
        
    print("Market indicators calculation successful")
    if hasattr(market_data, 'attrs') and 'indicators' in market_data.attrs:
        print(f"Market trend: {market_data.attrs['indicators']['short_term_trend']}")
    else:
        print("Market trend information not available")
    
    return True

if __name__ == "__main__":
    success = test_backtesting()
    print(f"\nTest {'succeeded' if success else 'failed'}") 