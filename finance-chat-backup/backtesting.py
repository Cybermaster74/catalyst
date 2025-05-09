import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

def backtest_strategy(df, analysis_date, stop_loss=0.05, take_profit=0.10):
    """
    Backtest the trading strategy and calculate 3-day and 5-day returns
    
    :param df: DataFrame with price data and indicators
    :param analysis_date: Date of analysis
    :param stop_loss: Stop loss percentage (default 5%)
    :param take_profit: Take profit percentage (default 10%)
    :return: Dictionary with backtest results
    """
    try:
        if df is None or df.empty:
            print("No data provided for backtesting")
            return None
            
        # Ensure we have enough data
        if len(df) < 20:  # Need at least 20 days for reliable backtesting
            print(f"Insufficient data points ({len(df)}) for backtesting")
            return None
        
        # Convert analysis_date to Timestamp if it's not already
        if not isinstance(analysis_date, pd.Timestamp):
            analysis_date = pd.Timestamp(analysis_date)
            
        # Get data after analysis date for backtesting
        future_data = df[df.index > pd.Timestamp(analysis_date)]
        if future_data.empty:
            print(f"No future data available for backtesting after {analysis_date}")
            return None
            
        # Get trading calendar for market days
        nyse = mcal.get_calendar('NYSE')
        
        # Get the next 20 trading days after analysis_date (extended to ensure we have enough)
        end_date = analysis_date + timedelta(days=30)  # Look ahead more days to ensure we have enough trading days
        trading_days = nyse.valid_days(start_date=analysis_date, end_date=end_date)
        
        print(f"Analysis date: {analysis_date}, Trading days available: {len(trading_days)}")
        
        # Get entry price (open price on analysis date or next trading day - for buying at market open)
        entry_date = None
        entry_price = None
        
        # First check if the analysis date is in the dataframe and is a trading day
        if analysis_date in df.index:
            entry_date = analysis_date
            entry_price = df.loc[analysis_date, 'Open'] if 'Open' in df.columns else df.loc[analysis_date, 'Close']
            print(f"Using analysis date as entry: {entry_date}")
        else:
            # Find the next trading day after analysis_date that exists in our data
            for day in trading_days:
                if day in df.index:
                    entry_date = day
                    entry_price = df.loc[day, 'Open'] if 'Open' in df.columns else df.loc[day, 'Close']
                    print(f"Analysis date {analysis_date} not found in data, using next trading day: {entry_date}")
                    break
        
        if entry_date is None or entry_price is None:
            print(f"Could not find a valid entry date/price after {analysis_date}")
            return None
            
        print(f"Entry date: {entry_date}, Entry price: ${entry_price:.2f}")
        
        # Convert all timestamps to normalized datetime format without timezone
        trading_days_norm = [pd.Timestamp(day).tz_localize(None).normalize() for day in trading_days]
        
        # Ensure all dataframe index timestamps are timezone naive
        df_index_normalized = []
        date_mapping = {}
        
        for idx in df.index:
            # Make the timestamp timezone naive if it has a timezone
            if hasattr(idx, 'tz') and idx.tz is not None:
                idx_naive = idx.tz_localize(None)
            else:
                idx_naive = idx
                
            # Normalize the timestamp (remove time portion)
            idx_norm = pd.Timestamp(idx_naive).normalize()
            df_index_normalized.append(idx_norm)
            
            # Map normalized timestamp to original index
            date_mapping[idx_norm] = idx
        
        # Find the trading days that are in our data
        valid_trading_days = []
        for day in trading_days_norm:
            if day in date_mapping:
                valid_trading_days.append(date_mapping[day])
        
        print(f"Found {len(valid_trading_days)} valid trading days in the data")
        
        # If we don't have valid trading days, try a more lenient approach
        if not valid_trading_days:
            print("No exact matches found. Trying closest date matching...")
            
            # For each trading day, find the closest date in our dataframe (within 1 day)
            for day in trading_days:
                # Ensure day is timezone naive
                if hasattr(day, 'tz') and day.tz is not None:
                    day_naive = day.tz_localize(None)
                else:
                    day_naive = day
                    
                day_norm = pd.Timestamp(day_naive).normalize()
                
                # Find dates within 1 day difference
                close_dates = []
                for idx, idx_norm in zip(df.index, df_index_normalized):
                    # Calculate the day difference safely (both dates are now naive)
                    days_diff = abs((idx_norm - day_norm).days)
                    if days_diff <= 1:
                        close_dates.append(idx)
                        
                if close_dates:
                    # Sort by proximity and add the closest
                    closest = min(close_dates, key=lambda x: abs(pd.Timestamp(x).normalize() - day_norm).days)
                    valid_trading_days.append(closest)
            
            print(f"Found {len(valid_trading_days)} close matching trading days")
        
        if not valid_trading_days:
            print("Could not find valid trading days for backtesting")
            return None
        
        # Sort the valid trading days
        valid_trading_days = sorted(valid_trading_days)
        
        # Find the index of our entry date
        # Make sure entry_date is timezone naive before normalizing
        if hasattr(entry_date, 'tz') and entry_date.tz is not None:
            entry_date_naive = entry_date.tz_localize(None)
        else:
            entry_date_naive = entry_date
            
        entry_date_norm = pd.Timestamp(entry_date_naive).normalize()
        entry_idx = None
        
        # Find the index of entry_date in valid_trading_days
        for i, day in enumerate(valid_trading_days):
            # Convert day to naive if it has timezone
            if hasattr(day, 'tz') and day.tz is not None:
                day_naive = day.tz_localize(None)
            else:
                day_naive = day
                
            if pd.Timestamp(day_naive).normalize() == entry_date_norm:
                entry_idx = i
                break
        
        if entry_idx is None:
            print(f"Entry date {entry_date} not found in valid trading days")
            # Try to find the closest day
            closest_idx = 0
            min_diff = float('inf')
            for i, day in enumerate(valid_trading_days):
                # Convert day to naive if it has timezone
                if hasattr(day, 'tz') and day.tz is not None:
                    day_naive = day.tz_localize(None)
                else:
                    day_naive = day
                
                diff = abs((pd.Timestamp(day_naive).normalize() - entry_date_norm).days)
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = i
            
            print(f"Using closest day at index {closest_idx} instead")
            entry_idx = closest_idx
        
        # Calculate 3-day return
        day3_date = None
        day3_price = None
        day3_return = None
        
        if entry_idx + 3 < len(valid_trading_days):
            day3_date = valid_trading_days[entry_idx + 3]
            day3_price = df.loc[day3_date, 'Close']
            day3_return = ((day3_price - entry_price) / entry_price) * 100
            print(f"3-day return date: {day3_date}, price: ${day3_price:.2f}, return: {day3_return:.2f}%")
        else:
            print(f"Not enough trading days for 3-day return (need {entry_idx + 3}, have {len(valid_trading_days)})")
        
        # Calculate 5-day return
        day5_date = None
        day5_price = None
        day5_return = None
        
        if entry_idx + 5 < len(valid_trading_days):
            day5_date = valid_trading_days[entry_idx + 5]
            day5_price = df.loc[day5_date, 'Close']
            day5_return = ((day5_price - entry_price) / entry_price) * 100
            print(f"5-day return date: {day5_date}, price: ${day5_price:.2f}, return: {day5_return:.2f}%")
        else:
            print(f"Not enough trading days for 5-day return (need {entry_idx + 5}, have {len(valid_trading_days)})")
        
        results = {
            'entry_price': entry_price,
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'day3_return': day3_return,
            'day3_date': day3_date.strftime('%Y-%m-%d') if day3_date is not None else None,
            'day3_price': day3_price,
            'day5_return': day5_return,
            'day5_date': day5_date.strftime('%Y-%m-%d') if day5_date is not None else None,
            'day5_price': day5_price
        }
        
        return results
        
    except Exception as e:
        print(f"Error in backtesting: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_win_rate(symbol, trends):
    """
    Calculate win rate based on stored trends.
    
    :param symbol: Stock symbol.
    :param trends: List of trend data.
    :return: Win rate statistics.
    """
    if not trends:
        return {"win_rate": 0, "total_trades": 0}
    
    # Count trades with positive returns
    wins = sum(1 for trend in trends if trend.get('direction') == 'up')
    
    # Calculate valid trades (ones with direction data)
    valid_trades = sum(1 for trend in trends if trend.get('direction') in ['up', 'down'])
    
    # Count stop loss and take profit triggers
    stop_loss_count = sum(1 for trend in trends if trend.get('reached_stop_loss', False))
    take_profit_count = sum(1 for trend in trends if trend.get('reached_take_profit', False))
    
    # Calculate win rate
    win_rate = (wins / valid_trades * 100) if valid_trades > 0 else 0
    
    # Calculate average return
    avg_return = sum(trend.get('actual_return', 0) for trend in trends if trend.get('actual_return') is not None) / valid_trades if valid_trades > 0 else 0
    
    # Calculate average missed opportunity
    missed_opps = [trend.get('max_potential_return', 0) - trend.get('actual_return', 0) 
                  for trend in trends 
                  if trend.get('max_potential_return') is not None and trend.get('actual_return') is not None]
    avg_missed_opportunity = sum(missed_opps) / len(missed_opps) if missed_opps else 0
    
    return {
        "win_rate": win_rate,
        "avg_return": avg_return,
        "total_trades": len(trends),
        "valid_trades": valid_trades,
        "stop_loss_triggered": stop_loss_count,
        "take_profit_triggered": take_profit_count,
        "stop_loss_percentage": (stop_loss_count / len(trends) * 100) if len(trends) > 0 else 0,
        "take_profit_percentage": (take_profit_count / len(trends) * 100) if len(trends) > 0 else 0,
        "avg_missed_opportunity": avg_missed_opportunity
    } 