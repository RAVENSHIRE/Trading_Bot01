"""
Streamlit Dashboard for Trading Bot
Real-time portfolio monitoring, backtest results, and signal analysis
"""

import sys
from pathlib import Path
import logging

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.portfolio import Portfolio
from data.multi_source_pipeline import MultiSourcePipeline
from analytics.duckdb_analytics import DuckDBAnalytics
from feature_store.features import FeatureEngineering
from optimization.optuna_tuner import ParameterTuner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio(initial_capital=100000)

if 'pipeline' not in st.session_state:
    st.session_state.pipeline = MultiSourcePipeline()

if 'analytics' not in st.session_state:
    st.session_state.analytics = DuckDBAnalytics()

if 'feature_eng' not in st.session_state:
    st.session_state.feature_eng = FeatureEngineering()


def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.title("📈 Trading Bot Dashboard")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()


def render_portfolio_metrics():
    """Render portfolio performance metrics"""
    st.header("Portfolio Metrics")
    
    portfolio = st.session_state.portfolio
    
    # Create dummy current prices for open positions
    current_prices = {}
    for symbol, position in portfolio.positions.items():
        if position.is_open:
            current_prices[symbol] = position.current_price
    
    summary = portfolio.get_summary(current_prices)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Value",
            f"${summary.get('nav', 0):,.2f}",
            f"${summary.get('total_pnl', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            "Cash",
            f"${summary.get('cash', 0):,.2f}",
            f"{(summary.get('cash', 0) / summary.get('nav', 1) * 100):.1f}%"
        )
    
    with col3:
        st.metric(
            "Leverage",
            f"{summary.get('leverage', 0):.2f}x",
            f"Return: {summary.get('return_pct', 0):.2f}%"
        )
    
    with col4:
        unrealized_pnl = summary.get('unrealized_pnl', 0)
        st.metric(
            "Unrealized P&L",
            f"${unrealized_pnl:,.2f}",
            f"{(unrealized_pnl / summary.get('nav', 1) * 100):.2f}%"
        )


def render_positions():
    """Render open positions"""
    st.subheader("Open Positions")
    
    portfolio = st.session_state.portfolio
    
    if portfolio.positions:
        positions_data = []
        for symbol, position in portfolio.positions.items():
            if position.is_open:
                # Use entry price as current price (would be updated in real system)
                current_price = position.entry_price
                pnl = position.calculate_pnl(current_price)
                
                positions_data.append({
                    'Symbol': symbol,
                    'Quantity': position.quantity,
                    'Entry Price': f"${position.entry_price:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'P&L': f"${pnl:.2f}",
                    'Return': f"{(pnl / (position.entry_price * abs(position.quantity) + 1e-10) * 100):.2f}%",
                    'Side': position.side.value
                })
        
        if positions_data:
            df_positions = pd.DataFrame(positions_data)
            st.dataframe(df_positions, use_container_width=True)
        else:
            st.info("No open positions")
    else:
        st.info("No open positions")


def render_data_sources():
    """Render data source controls"""
    st.header("Data Management")
    
    tab1, tab2, tab3 = st.tabs(["Market Data", "Fundamentals", "Analytics"])
    
    with tab1:
        st.subheader("Market Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbols_input = st.text_input(
                "Symbols (comma-separated)",
                value="AAPL,MSFT,GOOGL,NVDA",
                help="Enter stock symbols to fetch data"
            )
        
        with col2:
            days_back = st.slider(
                "Days of historical data",
                min_value=30,
                max_value=500,
                value=252,
                step=10
            )
        
        if st.button("📥 Fetch Market Data", use_container_width=True):
            with st.spinner("Fetching market data..."):
                symbols = [s.strip().upper() for s in symbols_input.split(",")]
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                try:
                    market_data = st.session_state.pipeline.fetch_market_data(
                        symbols, start_date, end_date
                    )
                    st.session_state.analytics.insert_market_data(market_data)
                    st.success(f"✅ Fetched {len(market_data)} data points")
                    
                    # Show data preview
                    st.subheader("Data Preview")
                    st.dataframe(market_data.head(10), use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error fetching data: {e}")
    
    with tab2:
        st.subheader("Fundamentals")
        
        symbols_fund = st.text_input(
            "Symbols for fundamentals",
            value="AAPL,MSFT,GOOGL",
            key="fundamentals_symbols"
        )
        
        if st.button("📊 Fetch Fundamentals", use_container_width=True):
            with st.spinner("Fetching fundamentals..."):
                symbols = [s.strip().upper() for s in symbols_fund.split(",")]
                
                try:
                    fundamentals = st.session_state.pipeline.fetch_fundamentals(symbols)
                    st.session_state.analytics.insert_fundamentals(fundamentals)
                    st.success(f"✅ Fetched fundamentals for {len(fundamentals)} companies")
                    
                    st.dataframe(fundamentals, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error fetching fundamentals: {e}")
    
    with tab3:
        st.subheader("Analytics Queries")
        
        query_type = st.selectbox(
            "Select query type",
            ["Stock Performance", "Momentum Screen", "Value Screen", "Correlation Matrix"]
        )
        
        if query_type == "Stock Performance":
            symbol = st.text_input("Symbol", value="AAPL").upper()
            days = st.slider("Days", 30, 500, 252)
            
            if st.button("Calculate"):
                perf = st.session_state.analytics.get_stock_performance(symbol, days)
                if perf:
                    st.json(perf)
                else:
                    st.warning("No data available")
        
        elif query_type == "Momentum Screen":
            min_return = st.slider("Minimum return (%)", 0.0, 50.0, 5.0)
            days = st.slider("Days", 30, 500, 60)
            
            if st.button("Screen"):
                momentum_stocks = st.session_state.analytics.get_momentum_screen(min_return, days)
                if not momentum_stocks.empty:
                    st.dataframe(momentum_stocks, use_container_width=True)
                else:
                    st.warning("No stocks match criteria")
        
        elif query_type == "Value Screen":
            max_pe = st.slider("Max P/E Ratio", 5.0, 50.0, 15.0)
            
            if st.button("Screen"):
                value_stocks = st.session_state.analytics.get_value_screen(max_pe)
                if not value_stocks.empty:
                    st.dataframe(value_stocks, use_container_width=True)
                else:
                    st.warning("No stocks match criteria")


def render_features():
    """Render feature engineering panel"""
    st.header("Feature Engineering")
    
    tab1, tab2 = st.tabs(["Technical Features", "Fundamental Features"])
    
    with tab1:
        st.subheader("Generate Technical Features")
        
        if st.button("🔧 Create Price Features", use_container_width=True):
            with st.spinner("Generating technical features..."):
                try:
                    # Create sample OHLCV data
                    dates = pd.date_range('2023-01-01', periods=252)
                    sample_ohlcv = pd.DataFrame({
                        'date': dates,
                        'open': 100 + np.cumsum(np.random.randn(252) * 2),
                        'high': 102 + np.cumsum(np.random.randn(252) * 2),
                        'low': 98 + np.cumsum(np.random.randn(252) * 2),
                        'close': 100 + np.cumsum(np.random.randn(252) * 2),
                        'volume': np.random.randint(1000000, 10000000, 252)
                    })
                    
                    features = st.session_state.feature_eng.create_price_features(sample_ohlcv)
                    
                    st.success("✅ Features generated")
                    st.write(f"Shape: {features.shape}")
                    st.dataframe(features.head(), use_container_width=True)
                    
                    # Feature statistics
                    st.subheader("Feature Statistics")
                    st.dataframe(features.describe(), use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Fundamental Features")
        st.info("Fundamental features require company data")


def render_optimization():
    """Render hyperparameter optimization panel"""
    st.header("Hyperparameter Optimization")
    
    signal_type = st.selectbox(
        "Select signal type to optimize",
        ["Momentum", "Mean Reversion"]
    )
    
    n_trials = st.slider(
        "Number of trials",
        min_value=10,
        max_value=200,
        value=50,
        step=10
    )
    
    if st.button("🚀 Start Optimization", use_container_width=True):
        with st.spinner(f"Optimizing {signal_type} signal..."):
            try:
                # Create sample data
                dates = pd.date_range('2023-01-01', periods=252)
                price_data = pd.DataFrame({
                    'date': dates,
                    'close': 100 + np.cumsum(np.random.randn(252) * 2),
                    'high': 102 + np.cumsum(np.random.randn(252) * 2),
                    'low': 98 + np.cumsum(np.random.randn(252) * 2),
                    'volume': np.random.randint(1000000, 10000000, 252)
                })
                
                tuner = ParameterTuner()
                params = tuner.tune_signal_parameters(
                    signal_type.lower(),
                    price_data,
                    n_trials=n_trials
                )
                
                st.success("✅ Optimization complete")
                st.json(params)
                
            except Exception as e:
                st.error(f"Error: {e}")


def main():
    """Main dashboard"""
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select page",
            ["Portfolio", "Data Sources", "Features", "Optimization", "Settings"]
        )
    
    # Page routing
    if page == "Portfolio":
        render_portfolio_metrics()
        render_positions()
    
    elif page == "Data Sources":
        render_data_sources()
    
    elif page == "Features":
        render_features()
    
    elif page == "Optimization":
        render_optimization()
    
    elif page == "Settings":
        st.header("Settings")
        st.info("Configuration options coming soon")


if __name__ == "__main__":
    main()
