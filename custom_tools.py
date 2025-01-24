import yfinance as yf
from langchain_core.tools import tool
from alpha_vantage.fundamentaldata import FundamentalData
from datetime import datetime,timedelta
from GoogleNews import GoogleNews

# 1 ###############################################################
@tool
def get_price_by_date(ticker, date):
    """
    Get the price of a stock ticker on a specific date.

    Parameters:
        ticker (str): Stock ticker symbol.
        date (str): Date in the format 'YYYY-MM-DD'.
    
    Returns:
        dict: Stock price details for the given date.

        Note : If stock is listed in NSE add .NS to the ticker symbol.
        For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        # Ensure the date is properly formatted
        datetime.strptime(date, '%Y-%m-%d')
        
        # Fetch the historical data
        stock = yf.Ticker(ticker)
        history = stock.history(start=date, end=(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=2)).strftime('%Y-%m-%d'))

        # Check if data is available for the date
        if history.empty:
            return {"error": f"No data available for {ticker} on {date}"}

        # Extract price details
        price = history['Close'].iloc[0]
        return {
            "ticker": ticker,
            "date": date,
            "close_price": price
        }
    except Exception as e:
        return {"error": f"Could not retrieve price for {ticker} on {date}: {str(e)}"}


@tool
def get_stock_price(ticker):
    """
    Get the current stock price for a given ticker symbol.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
    
    Returns:
        dict: Current stock price and metadata.

        Note : If stock is listed in NSE add .NS to the ticker symbol.
        For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")['Close'][-1]
        return {
            "ticker": ticker,
            "current_price": current_price,
            "currency": stock.info.get('currency', 'N/A'),
        }
    except Exception as e:
        return {"error": f"Could not retrieve price for {ticker}: {str(e)}"}

@tool
def get_price_history(ticker, period="1mo"):
    """
    Get the price history for a given ticker symbol over a specified period.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
        period (str): The time period (e.g., '1d', '5d', '1mo', '6mo', '1y', '5y', 'max').
    
    Returns:
        dict: Historical prices for the stock.

        Note : If stock is listed in NSE add .NS to the ticker symbol.
        For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        return history[['Open', 'High', 'Low', 'Close', 'Volume']].to_dict()
    except Exception as e:
        return {"error": f"Could not retrieve history for {ticker}: {str(e)}"}

@tool
def get_52_week_high_low(ticker):
    """
    Get the 52-week high and low prices for a given ticker symbol.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
    
    Returns:
        dict: 52-week high and low prices.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        high_52_week = stock.info.get('fiftyTwoWeekHigh', 'N/A')
        low_52_week = stock.info.get('fiftyTwoWeekLow', 'N/A')
        return {
            "ticker": ticker,
            "52_week_high": high_52_week,
            "52_week_low": low_52_week,
        }
    except Exception as e:
        return {"error": f"Could not retrieve 52-week high/low for {ticker}: {str(e)}"}

@tool
def get_market_trends(ticker):
    """
    Get market trends and basic stats for a given ticker symbol.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
    
    Returns:
        dict: Key market stats like market cap, PE ratio, etc.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        return {
            "ticker": ticker,
            "market_cap": stock.info.get('marketCap', 'N/A'),
            "pe_ratio": stock.info.get('trailingPE', 'N/A'),
            "dividend_yield": stock.info.get('dividendYield', 'N/A'),
            "beta": stock.info.get('beta', 'N/A'),
        }
    except Exception as e:
        return {"error": f"Could not retrieve market trends for {ticker}: {str(e)}"}
    
# 2 ###############################################################
@tool
def compare_stock_performance(ticker1, ticker2, period="1mo"):
    """
    Compare performance of two stocks over a specified period.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock1 = yf.Ticker(ticker1)
        stock2 = yf.Ticker(ticker2)
        history1 = stock1.history(period=period)['Close']
        history2 = stock2.history(period=period)['Close']
        return {
            "ticker1": ticker1,
            "ticker2": ticker2,
            "ticker1_performance": history1.pct_change().cumsum().iloc[-1],
            "ticker2_performance": history2.pct_change().cumsum().iloc[-1]
        }
    except Exception as e:
        return {"error": f"Could not compare stocks {ticker1} and {ticker2}: {str(e)}"}


@tool
def daily_performance(ticker):
    """
    Get the daily performance of a stock.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="2d")['Close']
        return {
            "ticker": ticker,
            "daily_change": (history.iloc[-1] - history.iloc[-2]) / history.iloc[-2] * 100
        }
    except Exception as e:
        return {"error": f"Could not retrieve daily performance for {ticker}: {str(e)}"}



@tool
def weekly_performance(ticker):
    """
    Get the weekly performance of a stock.
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="7d")['Close']
        return {
            "ticker": ticker,
            "weekly_change": (history.iloc[-1] - history.iloc[0]) / history.iloc[0] * 100
        }
    except Exception as e:
        return {"error": f"Could not retrieve weekly performance for {ticker}: {str(e)}"}


@tool
def sector_performance(sector_tickers, period="1mo"):
    """
    Calculate the average performance of a sector based on a list of tickers.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        performances = []
        for ticker in sector_tickers:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)['Close']
            performance = history.pct_change().cumsum().iloc[-1]
            performances.append(performance)
        return {
            "sector_performance": sum(performances) / len(performances),
            "individual_performances": dict(zip(sector_tickers, performances))
        }
    except Exception as e:
        return {"error": f"Could not calculate sector performance: {str(e)}"}



# 3 ###############################################################

ALPHA_VANTAGE_API_KEY = "YVQONQOHQHUY7EAJ"
fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY)

@tool
def recommend_stocks_for_long_term(sector=None):
    """
    Recommend stocks for long-term investment based on fundamental data.

    Parameters:
        sector (str): Optional sector filter (e.g., "Technology").
    
    Returns:
        list: Recommended stocks with high EPS and low P/E ratio.

    """
    try:
        # Replace this with a specific sector filter if needed
        data, _ = fd.get_sector_performance()
        recommended_stocks = []
        for symbol in data:
            stock = yf.Ticker(symbol)
            info = stock.info
            pe_ratio = info.get("trailingPE", None)
            eps = info.get("trailingEps", None)
            if pe_ratio and eps and eps > 2 and pe_ratio < 20:  # Example criteria
                recommended_stocks.append({
                    "ticker": symbol,
                    "name": info.get("longName", "Unknown"),
                    "pe_ratio": pe_ratio,
                    "eps": eps
                })
        return recommended_stocks
    except Exception as e:
        return {"error": f"Could not generate recommendations: {str(e)}"}


@tool
def check_growth_potential(ticker):
    """
    Check if a stock has growth potential based on EPS growth and revenue trends.

    Parameters:
        ticker (str): Stock ticker symbol.
    
    Returns:
        dict: Analysis of growth potential.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        eps_growth = info.get("earningsGrowth", None)
        revenue_growth = info.get("revenueGrowth", None)
        return {
            "ticker": ticker,
            "eps_growth": eps_growth,
            "revenue_growth": revenue_growth,
            "growth_potential": eps_growth > 0.1 and revenue_growth > 0.1  # Example criteria
        }
    except Exception as e:
        return {"error": f"Could not analyze growth potential for {ticker}: {str(e)}"}



@tool
def get_top_dividend_stocks():
    """
    Get stocks offering the highest dividends.

    Returns:
        list: Stocks with the highest dividend yields.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        # Replace with your preferred stock list
        stock_list = ["AAPL", "MSFT", "T", "JNJ", "PG"]
        dividend_stocks = []
        for ticker in stock_list:
            stock = yf.Ticker(ticker)
            info = stock.info
            dividend_yield = info.get("dividendYield", None)
            if dividend_yield:
                dividend_stocks.append({
                    "ticker": ticker,
                    "name": info.get("longName", "Unknown"),
                    "dividend_yield": dividend_yield * 100
                })
        return sorted(dividend_stocks, key=lambda x: x['dividend_yield'], reverse=True)
    except Exception as e:
        return {"error": f"Could not retrieve dividend stocks: {str(e)}"}



@tool
def assess_risk(ticker):
    """
    Assess the risk of investing in a stock based on volatility and beta.

    Parameters:
        ticker (str): Stock ticker symbol.
    
    Returns:
        dict: Risk assessment of the stock.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        beta = info.get("beta", None)
        volatility = stock.history(period="1y")['Close'].pct_change().std() * 100  # Annualized volatility
        return {
            "ticker": ticker,
            "beta": beta,
            "volatility": f"{volatility:.2f}%",
            "risk_level": "High" if beta > 1.2 or volatility > 30 else "Moderate" if beta > 0.8 else "Low"
        }
    except Exception as e:
        return {"error": f"Could not assess risk for {ticker}: {str(e)}"}



#Updates #######################################################

@tool
def get_premarket_price(ticker):
    """
    Retrieves the pre-market price for a given stock ticker.

    This function uses the `yfinance` library to fetch the most recent pre-market price 
    for a stock specified by its ticker symbol. It fetches the historical data for a single day
    with pre- and post-market data included, and extracts the most recent closing price.

    Args:
        ticker (str): The stock ticker symbol for which to retrieve the pre-market price.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The input stock ticker.
            - "pre_market_price" (float): The most recent pre-market closing price.
        
        If an error occurs, the dictionary will instead contain:
            - "error" (str): A description of the error.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    try:
        stock = yf.Ticker(ticker)
        pre_market_data = stock.history(period="1d", prepost=True)
        pre_market_price = pre_market_data['Close'].iloc[-1]
        return {"ticker": ticker, "pre_market_price": pre_market_price}
    except Exception as e:
        return {"error": f"Could not retrieve pre-market price for {ticker}: {str(e)}"}

import ssl

@tool 
def get_financial_news(ticker: str, num_results: int = 10):
    """
    Fetch financial news headlines for a given query using Google News.
    
    Parameters:
        query (str): The search query (e.g., stock ticker like 'AAPL').
        num_results (int): The maximum number of news headlines to return (default: 10).
    
    Returns:
        list: A list of dictionaries containing news headlines and their respective links.

    Note : If stock is listed in NSE add .NS to the ticker symbol.
    For example, for Reliance Industries Limited, the ticker symbol is RELIANCE.NS
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    googlenews = GoogleNews(lang='en')
    googlenews.search(f"Give news about {ticker}")
    
    # Fetch results
    results = googlenews.results()
    
    # Extract required number of results
    news_list = [
        {"title": result["title"]}
        for result in results[:num_results]
    ]
    
    return news_list



@tool
def get_present_date():
    """
    Get the current date formatted as '1 May 2025'.
    
    This function retrieves the current date and formats it in a human-readable
    style where:
        - The day is shown without a leading zero.
        - The full month name is displayed.
        - The year is in four digits.
    
    Returns:
        str: The current date in the format '1 May 2025'.
    """
    # Get the current date
    current_date = datetime.now()
    # Format the date in "1 May 2025" format
    formatted_date = current_date.strftime("%-d %B %Y")
    return formatted_date