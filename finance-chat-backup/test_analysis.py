import pandas as pd
from datetime import datetime, timedelta
from app import analyze_stock

def test_stock_analysis():
    """
    Test the full stock analysis functionality, including technical analysis, 
    sentiment analysis, and backtesting.
    """
    # Test with a known date
    analysis_date = datetime(2025, 4, 25)  # This is a Friday
    
    print(f"\nTesting full stock analysis with analysis date: {analysis_date}")
    
    # Analyze a common stock
    symbol = "AAPL"
    stop_loss = 0.05
    take_profit = 0.08
    
    # Run the full analysis
    print(f"Analyzing {symbol} with stop loss {stop_loss*100}% and take profit {take_profit*100}%")
    results = analyze_stock(symbol, analysis_date, stop_loss, take_profit)
    
    # Check if analysis was successful
    if "error" in results:
        print(f"Error in analysis: {results['error']}")
        return False
        
    # Print key results
    print(f"\nAnalysis Results for {symbol}:")
    print(f"Date: {results['date']}")
    
    if "recommendation" in results:
        print(f"Recommendation: {results['recommendation']}")
    
    if "sentiment_score" in results:
        print(f"Sentiment Score: {results['sentiment_score']:.4f}")
    
    if "signals" in results:
        signals = results["signals"]
        print("\nTechnical Signals:")
        if "overall_trend" in signals:
            print(f"Overall Trend: {signals['overall_trend']:.2f}")
        if "overall_momentum" in signals:
            print(f"Overall Momentum: {signals['overall_momentum']:.2f}")
        if "market_condition" in signals:
            print(f"Market Condition: {signals['market_condition']}")
    
    if "backtest_results" in results:
        backtest = results["backtest_results"]
        print("\nBacktest Results:")
        print(f"Entry Date: {backtest.get('entry_date', 'N/A')}")
        print(f"Entry Price: ${backtest.get('entry_price', 0):.2f}")
        
        if backtest.get('day3_date'):
            print(f"3-Day Date: {backtest.get('day3_date')}")
            print(f"3-Day Return: {backtest.get('day3_return', 0):.2f}%")
        else:
            print("3-Day Return: N/A")
            
        if backtest.get('day5_date'):
            print(f"5-Day Date: {backtest.get('day5_date')}")
            print(f"5-Day Return: {backtest.get('day5_return', 0):.2f}%")
        else:
            print("5-Day Return: N/A")
    
    print("\nAnalysis completed successfully")
    return True

if __name__ == "__main__":
    success = test_stock_analysis()
    print(f"\nTest {'succeeded' if success else 'failed'}") 