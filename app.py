from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat_pipeline import chat
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import os
from typing import List, Dict, Any
import asyncio
from datetime import datetime

load_dotenv()

USER_AGENT = "financeGPT/1.0 (mailto:financegpt@gmail.com)"
yf.utils.user_agent = USER_AGENT 
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Allow all origins
    allow_credentials=True,      # Allow cookies and authentication headers
    allow_methods=["*"],         # Allow all HTTP methods
    allow_headers=["*"],         # Allow all headers
)

# Define Pydantic models
class ChatRequest(BaseModel):
    query: str

class PriceRequest(BaseModel):
    ticker: str

class MultipleTickerPriceRequest(BaseModel):
    ticker_list: List[str]

# -----------------------------------------------------------------------------
# Cache Classes
# -----------------------------------------------------------------------------
class CacheSection:
    def __init__(self):
        # We will store the data in a dictionary keyed by ticker
        self.data: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

class Cache:
    def __init__(self):
        self.stats = CacheSection()
        self.nasdaq_top50 = CacheSection()
        self.bse_top50 = CacheSection()

cache = Cache()

# -----------------------------------------------------------------------------
# Ticker Lists
# -----------------------------------------------------------------------------
NASDAQ_TOP_50 = [
    'AAPL', 'MSFT', 'AMZN', 'GOOG', 'GOOGL', 'NVDA', 'TSLA', 'META', 'PEP', 'AVGO',
    'COST', 'CSCO', 'ADBE', 'TXN', 'CMCSA', 'NFLX', 'AMD', 'INTC', 'QCOM', 'HON',
    'AMGN', 'ORLY', 'GILD', 'MDLZ', 'ADP', 'PYPL', 'ISRG', 'REGN', 'ADI', 'SBUX',
    'MU', 'LRCX', 'VRTX', 'BKNG', 'ACN', 'KDP', 'MAR', 'CDNS', 'MNST', 'CTAS',
    'TEAM', 'PANW', 'XEL', 'MRNA', 'AEP', 'FAST', 'EXC', 'SNPS', 'DXCM', 'FTNT'
]

BSE_TOP_50 = [
    'RELIANCE.BO', 'TCS.BO', 'HDFCBANK.BO', 'INFY.BO', 'MRF.NS', 'ICICIBANK.BO',
    'HINDUNILVR.BO', 'ITC.BO', 'KOTAKBANK.BO', 'BAJFINANCE.BO', 'SBIN.BO',
    'BHARTIARTL.BO', 'ASIANPAINT.BO', 'MARUTI.BO', 'DMART.BO', 'WIPRO.BO',
    'ADANIGREEN.BO', 'LT.BO', 'SUNPHARMA.BO', 'TECHM.BO', 'ULTRACEMCO.BO',
    'NTPC.BO', 'POWERGRID.BO', 'TITAN.BO', 'ONGC.BO', 'M&M.BO', 'JSWSTEEL.BO',
    'BAJAJFINSV.BO', 'HCLTECH.BO', 'GRASIM.BO', 'COALINDIA.BO', 'HEROMOTOCO.BO',
    'SBILIFE.BO', 'ADANIPORTS.BO', 'EICHERMOT.BO', 'DRREDDY.BO', 'BPCL.BO',
    'HDFCLIFE.BO', 'DABUR.BO', 'BRITANNIA.BO', 'DIVISLAB.BO', 'VEDL.BO',
    'ICICIPRULI.BO', 'GODREJCP.BO', 'SHREECEM.BO', 'PIDILITIND.BO',
    'TATAMOTORS.BO', 'INDUSINDBK.BO', 'APOLLOHOSP.BO', 'CIPLA.BO'
]

PREDEFINED_STATS_TICKERS = ['AAPL', 'MSFT', 'GOOG', 'RELIANCE.NS', 'ADANIENT.NS', 'TATAMOTORS.NS']

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def fetch_bulk_stock_data_sync(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Synchronously fetch bulk stock data for a list of tickers.
    Returns a dict keyed by ticker with stock info as value.
    """
    stock_data = {}
    try:
        tickers_str = " ".join(tickers)
        data = yf.Tickers(tickers_str)

        for ticker in tickers:
            stock = data.tickers.get(ticker)
            if not stock:
                print(f"[{datetime.now()}] No data found for ticker: {ticker}")
                continue

            info = stock.info
            history = stock.history(period="1d")

            # Check if history data is present
            if history.empty:
                print(f"[{datetime.now()}] Empty history data for ticker: {ticker}")
                continue

            close_price = history['Close'].iloc[-1]
            open_price = history['Open'].iloc[-1]
            price = round(close_price, 2)
            change = round(close_price - open_price, 2)
            change_percent = round((change / open_price) * 100, 2) if open_price != 0 else 0

            # Convert Market Cap to Billions and Volume to Millions
            market_cap = (
                round(info.get('marketCap', 0) / 1e9, 2)
                if info.get('marketCap') else 'N/A'
            )
            volume = (
                round(info.get('regularMarketVolume', 0) / 1e6, 2)
                if info.get('regularMarketVolume') else 'N/A'
            )
            avg_volume = (
                round(info.get('averageVolume', 0) / 1e6, 2)
                if info.get('averageVolume') else 'N/A'
            )
            pe_ratio = (
                round(info.get('trailingPE', 0), 2)
                if info.get('trailingPE') else 'N/A'
            )
            change_52wk = (
                round(info.get('52WeekChange', 0) * 100, 2)
                if info.get('52WeekChange') else 'N/A'
            )

            stock_data[ticker.upper()] = {
                'Symbol': ticker.upper(),
                'Name': info.get('shortName', 'N/A'),
                'Price': price,
                'Change': change,
                'Change %': change_percent,
                'Volume (M)': volume,
                'Avg Vol (3M) (M)': avg_volume,
                'Market Cap (B)': market_cap,
                'P/E Ratio (TTM)': pe_ratio,
                '52 WK Change %': change_52wk
            }
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching bulk stock data: {e}")
    return stock_data

def fetch_stats_data_sync(ticker_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Synchronously fetch stats data for a list of tickers.
    Returns a dict keyed by ticker with stats info as value.
    """
    stats_data: Dict[str, Dict[str, Any]] = {}
    try:
        tickers_str = " ".join(ticker_list)
        data = yf.Tickers(tickers_str)

        for ticker in ticker_list:
            stock = data.tickers.get(ticker)
            if not stock:
                print(f"[{datetime.now()}] No data found for ticker: {ticker}")
                continue

            info = stock.info
            history = stock.history(period="5d")  # Ensure enough data for `iloc[-2]`

            # Check if history has at least 2 entries
            if len(history) < 2:
                print(f"[{datetime.now()}] Not enough history data for ticker: {ticker}")
                continue

            current_price = history['Close'].iloc[-1]
            yesterday_price = history['Close'].iloc[-2]
            company_name = info.get('longName', 'N/A')

            percentage_change = 0
            if yesterday_price != 0:
                percentage_change = ((current_price - yesterday_price) / yesterday_price) * 100

            if percentage_change > 0:
                percentage_change_str = f"+{percentage_change:.2f}%"
                change = "positive"
            elif percentage_change < 0:
                percentage_change_str = f"{percentage_change:.2f}%"
                change = "negative"
            else:
                percentage_change_str = f"{percentage_change:.2f}%"
                change = "same"

            stats_data[ticker.upper()] = {
                "ticker": ticker.upper(),
                "company_name": company_name,
                "current_price": current_price,
                "currency": info.get('currency', 'N/A'),
                "percentage_change": percentage_change_str,
                "change": change
            }
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching stats data: {e}")
    return stats_data

# -----------------------------------------------------------------------------
# Asynchronous Wrappers
# -----------------------------------------------------------------------------
async def fetch_bulk_stock_data(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Asynchronously fetch bulk stock data.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_bulk_stock_data_sync, tickers)

async def fetch_stats_data(ticker_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Asynchronously fetch stats data.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_stats_data_sync, ticker_list)

# -----------------------------------------------------------------------------
# Periodic Update Tasks
# -----------------------------------------------------------------------------
async def update_stats_periodically():
    """
    Background task to update stats every 10 seconds.
    Partially updates the cache so existing data doesn't get lost
    if some tickers fail to fetch.
    """
    while True:
        try:
            print(f"[{datetime.now()}] Starting stats cache update...")
            new_stats = await fetch_stats_data(PREDEFINED_STATS_TICKERS)
            if new_stats:
                async with cache.stats.lock:
                    # Partial update of stats cache
                    for ticker, info in new_stats.items():
                        cache.stats.data[ticker] = info
                print(f"[{datetime.now()}] Stats cache updated successfully.")
            else:
                print(f"[{datetime.now()}] Stats cache update skipped due to empty data.")
        except Exception as e:
            print(f"[{datetime.now()}] Error updating stats cache: {e}")
        await asyncio.sleep(10)  # Wait 10 seconds before next update

async def update_nasdaq_bse_periodically():
    """
    Background task to update NASDAQ and BSE Top 50 every 30 seconds.
    Partially updates the cache so existing data doesn't get lost
    if some tickers fail to fetch.
    """
    while True:
        try:
            print(f"[{datetime.now()}] Starting NASDAQ and BSE cache update...")
            # Update NASDAQ Top 50
            new_nasdaq = await fetch_bulk_stock_data(NASDAQ_TOP_50)
            if new_nasdaq:
                async with cache.nasdaq_top50.lock:
                    # Partial update
                    for ticker, info in new_nasdaq.items():
                        cache.nasdaq_top50.data[ticker] = info
                print(f"[{datetime.now()}] NASDAQ Top 50 cache updated successfully.")
            else:
                print(f"[{datetime.now()}] NASDAQ Top 50 cache update skipped due to empty data.")

            # Update BSE Top 50
            new_bse = await fetch_bulk_stock_data(BSE_TOP_50)
            if new_bse:
                async with cache.bse_top50.lock:
                    # Partial update
                    for ticker, info in new_bse.items():
                        cache.bse_top50.data[ticker] = info
                print(f"[{datetime.now()}] BSE Top 50 cache updated successfully.")
            else:
                print(f"[{datetime.now()}] BSE Top 50 cache update skipped due to empty data.")
        except Exception as e:
            print(f"[{datetime.now()}] Error updating NASDAQ/BSE cache: {e}")
        await asyncio.sleep(30)  # Wait 30 seconds before next update

# -----------------------------------------------------------------------------
# Startup Event
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Start background tasks on application startup.
    """
    asyncio.create_task(update_stats_periodically())
    asyncio.create_task(update_nasdaq_bse_periodically())

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to handle chat queries.
    """
    try:
        answer = chat(request.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_price")
async def get_price_endpoint(request: PriceRequest):
    """
    Endpoint to get the price of a single ticker.
    Serves data from the centralized cache.
    """
    try:
        ticker = request.ticker.upper()
        # Search NASDAQ Top 50
        async with cache.nasdaq_top50.lock:
            nasdaq_data = dict(cache.nasdaq_top50.data)
        if ticker in nasdaq_data:
            return {"price": nasdaq_data[ticker]}

        # Search BSE Top 50
        async with cache.bse_top50.lock:
            bse_data = dict(cache.bse_top50.data)
        if ticker in bse_data:
            return {"price": bse_data[ticker]}

        # Search Stats
        async with cache.stats.lock:
            stats_data = dict(cache.stats.data)
        if ticker in stats_data:
            return {"price": stats_data[ticker]}

        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_multiple_prices")
async def get_multiple_prices_endpoint(request: MultipleTickerPriceRequest):
    """
    Endpoint to get prices for multiple tickers.
    Serves data from the centralized cache.
    """
    try:
        tickers = [t.upper() for t in request.ticker_list]
        prices = []

        # Search NASDAQ Top 50
        async with cache.nasdaq_top50.lock:
            nasdaq_data = dict(cache.nasdaq_top50.data)
        for t in tickers:
            if t in nasdaq_data:
                prices.append(nasdaq_data[t])

        # Search BSE Top 50
        async with cache.bse_top50.lock:
            bse_data = dict(cache.bse_top50.data)
        for t in tickers:
            if t in bse_data:
                prices.append(bse_data[t])

        # Search Stats
        async with cache.stats.lock:
            stats_data = dict(cache.stats.data)
        for t in tickers:
            if t in stats_data:
                prices.append(stats_data[t])

        if not prices:
            raise HTTPException(status_code=404, detail="No valid tickers found.")

        return {"prices": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_stats")
async def get_stats_endpoint():
    """
    Endpoint to get statistics for a predefined list of tickers.
    Serves data from the centralized cache.
    """
    try:
        async with cache.stats.lock:
            stats_data = dict(cache.stats.data)
        # Filter stats for predefined tickers
        filtered_stats = [stats_data[t] for t in PREDEFINED_STATS_TICKERS if t in stats_data]
        return {"ticker_data": filtered_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nasdaq-top50")
async def nasdaq_top50_endpoint():
    """
    Endpoint to get data for NASDAQ top 50 companies.
    Serves data from the centralized cache.
    """
    try:
        async with cache.nasdaq_top50.lock:
            data_dict = dict(cache.nasdaq_top50.data)
        # Convert dict to list
        table_data = list(data_dict.values())
        return {"table_data": table_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bse-top50")
async def bse_top50_endpoint():
    """
    Endpoint to get data for BSE top 50 companies.
    Serves data from the centralized cache.
    """
    try:
        async with cache.bse_top50.lock:
            data_dict = dict(cache.bse_top50.data)
        # Convert dict to list
        table_data = list(data_dict.values())
        return {"table_data": table_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))