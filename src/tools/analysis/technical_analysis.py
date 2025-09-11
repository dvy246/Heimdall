"""
Technical analysis tools for stock market data.

This module provides tools for technical analysis using yfinance and pandas_ta,
including comprehensive technical indicators, historical price data validation,
and consistent indicator calculations with proper error handling.
"""

import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import warnings
from datetime import datetime, timedelta
from typing import Dict, Any
from langchain_core.tools import tool
from src.config.looging_config import logger

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class TechnicalAnalysisError(Exception):
    """Custom exception for technical analysis errors."""
    pass


def _validate_ticker(ticker: str) -> str:
    """
    Validates ticker symbol format.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Validated ticker symbol
        
    Raises:
        ValueError: If ticker format is invalid
    """
    if not isinstance(ticker, str):
        raise ValueError("Ticker must be a string")
    
    ticker = ticker.upper().strip()
    
    if not ticker:
        raise ValueError("Ticker cannot be empty")
    
    if len(ticker) > 10:
        raise ValueError("Ticker symbol too long (max 10 characters)")
    
    # Allow alphanumeric characters, dots, and hyphens for international tickers
    if not all(c.isalnum() or c in '.-' for c in ticker):
        raise ValueError("Ticker contains invalid characters")
    
    return ticker


def _validate_period(period: str) -> str:
    """
    Validates yfinance period parameter.
    
    Args:
        period: Time period for historical data
        
    Returns:
        Validated period
        
    Raises:
        ValueError: If period is invalid
    """
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    if period not in valid_periods:
        raise ValueError(f"Period must be one of {valid_periods}, got: {period}")
    
    return period


def _calculate_technical_indicators(hist: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive technical indicators for historical data.
    
    Args:
        hist: Historical price data DataFrame
        
    Returns:
        DataFrame with technical indicators added
        
    Raises:
        TechnicalAnalysisError: If indicator calculation fails
    """
    try:
        # Ensure column names are properly formatted
        hist.columns = [col.capitalize() for col in hist.columns]
        
        # Calculate basic indicators
        hist.ta.rsi(append=True)
        hist.ta.sma(length=20, append=True)
        hist.ta.sma(length=50, append=True)
        hist.ta.sma(length=200, append=True)
        hist.ta.ema(length=12, append=True)
        hist.ta.ema(length=26, append=True)
        
        # Calculate MACD
        hist.ta.macd(append=True)
        
        # Calculate Bollinger Bands
        hist.ta.bbands(append=True)
        
        # Calculate additional indicators
        hist.ta.stoch(append=True)  # Stochastic oscillator
        hist.ta.adx(append=True)    # Average Directional Index
        hist.ta.atr(append=True)    # Average True Range
        
        # Calculate volume indicators if volume data is available
        if 'Volume' in hist.columns and not hist['Volume'].isna().all():
            hist.ta.obv(append=True)  # On Balance Volume
            hist.ta.vwap(append=True)  # Volume Weighted Average Price
        
        return hist
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        raise TechnicalAnalysisError(f"Failed to calculate technical indicators: {str(e)}")


def _extract_latest_indicators(hist: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract the latest values of technical indicators.
    
    Args:
        hist: Historical data with technical indicators
        
    Returns:
        Dict containing latest indicator values
    """
    indicators = {}
    
    # Basic price data
    if 'Close' in hist.columns:
        indicators['current_price'] = hist['Close'].iloc[-1]
    if 'Volume' in hist.columns:
        indicators['current_volume'] = hist['Volume'].iloc[-1]
    
    # Moving averages
    for col in hist.columns:
        if col.startswith('SMA_'):
            indicators[col.lower()] = hist[col].iloc[-1]
        elif col.startswith('EMA_'):
            indicators[col.lower()] = hist[col].iloc[-1]
    
    # RSI
    if 'RSI_14' in hist.columns:
        indicators['rsi'] = hist['RSI_14'].iloc[-1]
    
    # MACD
    if 'MACD_12_26_9' in hist.columns:
        indicators['macd'] = hist['MACD_12_26_9'].iloc[-1]
    if 'MACDh_12_26_9' in hist.columns:
        indicators['macd_histogram'] = hist['MACDh_12_26_9'].iloc[-1]
    if 'MACDs_12_26_9' in hist.columns:
        indicators['macd_signal'] = hist['MACDs_12_26_9'].iloc[-1]
    
    # Bollinger Bands
    if 'BBU_20_2.0' in hist.columns:
        indicators['bb_upper'] = hist['BBU_20_2.0'].iloc[-1]
    if 'BBM_20_2.0' in hist.columns:
        indicators['bb_middle'] = hist['BBM_20_2.0'].iloc[-1]
    if 'BBL_20_2.0' in hist.columns:
        indicators['bb_lower'] = hist['BBL_20_2.0'].iloc[-1]
    
    # Stochastic
    if 'STOCHk_14_3_3' in hist.columns:
        indicators['stoch_k'] = hist['STOCHk_14_3_3'].iloc[-1]
    if 'STOCHd_14_3_3' in hist.columns:
        indicators['stoch_d'] = hist['STOCHd_14_3_3'].iloc[-1]
    
    # ADX
    if 'ADX_14' in hist.columns:
        indicators['adx'] = hist['ADX_14'].iloc[-1]
    
    # ATR
    if 'ATR_14' in hist.columns:
        indicators['atr'] = hist['ATR_14'].iloc[-1]
    
    # Volume indicators
    if 'OBV' in hist.columns:
        indicators['obv'] = hist['OBV'].iloc[-1]
    if 'VWAP_D' in hist.columns:
        indicators['vwap'] = hist['VWAP_D'].iloc[-1]
    
    return indicators


def _generate_technical_signals(indicators: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate trading signals based on technical indicators.
    
    Args:
        indicators: Dictionary of technical indicator values
        
    Returns:
        Dict containing trading signals and interpretations
    """
    signals = {}
    
    # RSI signals
    if 'rsi' in indicators:
        rsi = indicators['rsi']
        if pd.notna(rsi):
            if rsi > 70:
                signals['rsi_signal'] = 'Overbought'
            elif rsi < 30:
                signals['rsi_signal'] = 'Oversold'
            else:
                signals['rsi_signal'] = 'Neutral'
    
    # Moving average signals
    current_price = indicators.get('current_price')
    if current_price and pd.notna(current_price):
        if 'sma_50' in indicators and pd.notna(indicators['sma_50']):
            if current_price > indicators['sma_50']:
                signals['sma_50_signal'] = 'Above SMA50 (Bullish)'
            else:
                signals['sma_50_signal'] = 'Below SMA50 (Bearish)'
        
        if 'sma_200' in indicators and pd.notna(indicators['sma_200']):
            if current_price > indicators['sma_200']:
                signals['sma_200_signal'] = 'Above SMA200 (Long-term Bullish)'
            else:
                signals['sma_200_signal'] = 'Below SMA200 (Long-term Bearish)'
    
    # MACD signals
    if 'macd' in indicators and 'macd_signal' in indicators:
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        if pd.notna(macd) and pd.notna(macd_signal):
            if macd > macd_signal:
                signals['macd_signal'] = 'Bullish Crossover'
            else:
                signals['macd_signal'] = 'Bearish Crossover'
    
    # Bollinger Bands signals
    if all(key in indicators for key in ['bb_upper', 'bb_lower']) and current_price:
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        if pd.notna(bb_upper) and pd.notna(bb_lower) and pd.notna(current_price):
            if current_price > bb_upper:
                signals['bb_signal'] = 'Above Upper Band (Overbought)'
            elif current_price < bb_lower:
                signals['bb_signal'] = 'Below Lower Band (Oversold)'
            else:
                signals['bb_signal'] = 'Within Bands (Normal)'
    
    return signals


@tool(description='gets the technichal analyses of the ticker')
def get_technical_analysis(
    ticker: str, 
    period: str = "1y",
    include_signals: bool = True
) -> Dict[str, Any]:
    """
    Fetches historical stock data and calculates comprehensive technical indicators.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        period: Time period for analysis (default: '1y')
        include_signals: Whether to include trading signals (default: True)
        
    Returns:
        Dict containing technical analysis data and indicators, or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        logger.info(f"Performing technical analysis for {ticker} over {period}")
        
        # Fetch historical data
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            logger.warning(f"No historical data found for ticker {ticker}")
            return {"error": f"No historical data found for ticker {ticker}"}
        
        # Calculate technical indicators
        hist_with_indicators = _calculate_technical_indicators(hist)
        
        # Extract latest indicator values
        latest_indicators = _extract_latest_indicators(hist_with_indicators)
        
        # Check for NaN values in critical indicators
        critical_indicators = ['current_price', 'rsi', 'sma_50', 'sma_200']
        for indicator in critical_indicators:
            if indicator in latest_indicators and pd.isna(latest_indicators[indicator]):
                logger.warning(f"Could not calculate {indicator} for {ticker} due to insufficient data")
                return {"error": f"Could not calculate {indicator} for {ticker}. Not enough data."}
        
        # Generate trading signals if requested
        signals = {}
        if include_signals:
            signals = _generate_technical_signals(latest_indicators)
        
        # Compile result
        result = {
            "ticker": ticker,
            "analysis_period": period,
            "data_points": len(hist),
            "last_updated": hist.index[-1].strftime('%Y-%m-%d') if not hist.empty else None,
            "indicators": latest_indicators,
            "signals": signals if include_signals else {},
            "summary": {
                "trend": _determine_trend(latest_indicators),
                "volatility": _assess_volatility(latest_indicators),
                "momentum": _assess_momentum(latest_indicators)
            }
        }
        
        logger.info(f"Successfully completed technical analysis for {ticker}")
        return result
        
    except (ValueError, TechnicalAnalysisError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_technical_analysis: {e}", exc_info=True)
        return {"error": f"Unexpected error while fetching technical analysis: {str(e)}"}


def _determine_trend(indicators: Dict[str, Any]) -> str:
    """Determine overall trend based on indicators."""
    try:
        current_price = indicators.get('current_price')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        
        if all(pd.notna(val) for val in [current_price, sma_50, sma_200]):
            if current_price > sma_50 > sma_200:
                return "Strong Uptrend"
            elif current_price > sma_50 and current_price > sma_200:
                return "Uptrend"
            elif current_price < sma_50 < sma_200:
                return "Strong Downtrend"
            elif current_price < sma_50 and current_price < sma_200:
                return "Downtrend"
            else:
                return "Sideways/Mixed"
        
        return "Insufficient data"
    except Exception:
        return "Unable to determine"


def _assess_volatility(indicators: Dict[str, Any]) -> str:
    """Assess volatility based on ATR and Bollinger Bands."""
    try:
        atr = indicators.get('atr')
        current_price = indicators.get('current_price')
        
        if pd.notna(atr) and pd.notna(current_price) and current_price > 0:
            atr_percentage = (atr / current_price) * 100
            if atr_percentage > 5:
                return "High"
            elif atr_percentage > 2:
                return "Medium"
            else:
                return "Low"
        
        return "Unable to assess"
    except Exception:
        return "Unable to assess"


def _assess_momentum(indicators: Dict[str, Any]) -> str:
    """Assess momentum based on RSI and MACD."""
    try:
        rsi = indicators.get('rsi')
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        
        momentum_score = 0
        
        if pd.notna(rsi):
            if rsi > 60:
                momentum_score += 1
            elif rsi < 40:
                momentum_score -= 1
        
        if pd.notna(macd) and pd.notna(macd_signal):
            if macd > macd_signal:
                momentum_score += 1
            else:
                momentum_score -= 1
        
        if momentum_score > 0:
            return "Positive"
        elif momentum_score < 0:
            return "Negative"
        else:
            return "Neutral"
    except Exception:
        return "Unable to assess"


@tool(description="Gets historical price data for a stock ticker")
def get_historical_prices(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> Dict[str, Any]:
    """
    Fetches historical price data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period for data (default: '1y')
        interval: Data interval (default: '1d')
        
    Returns:
        Dict containing historical price data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
        if interval not in valid_intervals:
            interval = '1d'
            logger.warning(f"Invalid interval provided, using default: {interval}")
        
        logger.info(f"Fetching historical prices for {ticker}")
        
        # Fetch data
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": f"No historical data found for ticker {ticker}"}
        
        # Convert to serializable format
        price_data = []
        for date, row in hist.iterrows():
            price_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "open": float(row['Open']) if pd.notna(row['Open']) else None,
                "high": float(row['High']) if pd.notna(row['High']) else None,
                "low": float(row['Low']) if pd.notna(row['Low']) else None,
                "close": float(row['Close']) if pd.notna(row['Close']) else None,
                "volume": int(row['Volume']) if pd.notna(row['Volume']) else None
            })
        
        result = {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "data_points": len(price_data),
            "start_date": price_data[0]["date"] if price_data else None,
            "end_date": price_data[-1]["date"] if price_data else None,
            "price_data": price_data
        }
        
        logger.info(f"Successfully fetched {len(price_data)} price data points for {ticker}")
        return result
        
    except (ValueError, TechnicalAnalysisError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_historical_prices: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}