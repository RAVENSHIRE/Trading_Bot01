"""
DuckDB Analytics Layer
High-performance analytical queries on financial data
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import pandas as pd
import duckdb

logger = logging.getLogger(__name__)


class DuckDBAnalytics:
    """DuckDB-based analytics engine for financial data"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "qsconnect.duckdb"
        
        self.db_path = str(db_path)
        self.conn = duckdb.connect(self.db_path)
        self._initialize_db()
        logger.info(f"Connected to DuckDB: {self.db_path}")
    
    def _initialize_db(self):
        """Create necessary tables if they don't exist"""
        
        # Market data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                date DATE,
                symbol VARCHAR,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume INTEGER,
                adj_close FLOAT
            )
        """)
        
        # Fundamentals table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fundamentals (
                symbol VARCHAR PRIMARY KEY,
                market_cap BIGINT,
                pe_ratio FLOAT,
                dividend_yield FLOAT,
                fifty_two_week_high FLOAT,
                fifty_two_week_low FLOAT,
                beta FLOAT,
                book_value FLOAT,
                updated_date DATE
            )
        """)
        
        # Financial ratios table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_ratios (
                symbol VARCHAR,
                date DATE,
                pe_ratio FLOAT,
                pb_ratio FLOAT,
                roe FLOAT,
                roa FLOAT,
                debt_equity FLOAT,
                current_ratio FLOAT,
                quick_ratio FLOAT
            )
        """)
        
        # Signals table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                date DATE,
                symbol VARCHAR,
                signal_type VARCHAR,
                strength FLOAT,
                entry_price FLOAT,
                stop_loss FLOAT,
                take_profit FLOAT
            )
        """)
        
        # Trades table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY,
                symbol VARCHAR,
                entry_date DATE,
                exit_date DATE,
                entry_price FLOAT,
                exit_price FLOAT,
                quantity INTEGER,
                pnl FLOAT,
                return_pct FLOAT,
                signal_type VARCHAR
            )
        """)
        
        logger.info("DuckDB tables initialized")
    
    def insert_market_data(self, df: pd.DataFrame):
        """Insert market data into DuckDB"""
        self.conn.register('temp_market_data', df)
        self.conn.execute("""
            INSERT INTO market_data 
            SELECT * FROM temp_market_data
            WHERE NOT EXISTS (
                SELECT 1 FROM market_data md
                WHERE md.date = temp_market_data.date 
                AND md.symbol = temp_market_data.symbol
            )
        """)
        self.conn.unregister('temp_market_data')
        logger.info(f"Inserted {len(df)} rows of market data")
    
    def insert_fundamentals(self, df: pd.DataFrame):
        """Insert fundamentals into DuckDB"""
        self.conn.register('temp_fundamentals', df)
        self.conn.execute("""
            DELETE FROM fundamentals WHERE symbol IN (SELECT DISTINCT symbol FROM temp_fundamentals)
        """)
        self.conn.execute("""
            INSERT INTO fundamentals SELECT * FROM temp_fundamentals
        """)
        self.conn.unregister('temp_fundamentals')
        logger.info(f"Inserted {len(df)} fundamentals records")
    
    def get_stock_performance(self, symbol: str, days: int = 252) -> Dict:
        """Calculate stock performance metrics"""
        query = f"""
            SELECT 
                symbol,
                MIN(date) as start_date,
                MAX(date) as end_date,
                FIRST(close) as start_price,
                LAST(close) as end_price,
                (LAST(close) - FIRST(close)) / FIRST(close) * 100 as return_pct,
                MAX(close) as high,
                MIN(close) as low,
                COUNT(*) as trading_days
            FROM market_data
            WHERE symbol = '{symbol}'
            AND date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY symbol
        """
        result = self.conn.execute(query).fetchall()
        
        if result:
            cols = ['symbol', 'start_date', 'end_date', 'start_price', 'end_price', 'return_pct', 'high', 'low', 'trading_days']
            return dict(zip(cols, result[0]))
        return {}
    
    def get_correlation_matrix(self, symbols: List[str], days: int = 252) -> pd.DataFrame:
        """Calculate correlation matrix for symbols"""
        placeholders = ','.join([f"'{s}'" for s in symbols])
        
        query = f"""
            SELECT 
                date,
                symbol,
                close
            FROM market_data
            WHERE symbol IN ({placeholders})
            AND date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY date, symbol
        """
        
        df = self.conn.execute(query).df()
        pivot_df = df.pivot(index='date', columns='symbol', values='close')
        
        # Calculate returns
        returns = pivot_df.pct_change().dropna()
        
        # Calculate correlation
        correlation = returns.corr()
        return correlation
    
    def get_momentum_screen(self, min_return: float = 0.05, days: int = 60) -> pd.DataFrame:
        """Find stocks with positive momentum"""
        query = f"""
            SELECT 
                symbol,
                FIRST(close) as start_price,
                LAST(close) as end_price,
                (LAST(close) - FIRST(close)) / FIRST(close) * 100 as return_pct,
                COUNT(*) as trading_days
            FROM market_data
            WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY symbol
            HAVING (LAST(close) - FIRST(close)) / FIRST(close) > {min_return / 100}
            ORDER BY return_pct DESC
        """
        
        return self.conn.execute(query).df()
    
    def get_value_screen(self, max_pe: float = 15.0) -> pd.DataFrame:
        """Find value stocks based on P/E ratio"""
        query = f"""
            SELECT 
                f.symbol,
                f.pe_ratio,
                f.pb_ratio,
                f.roe,
                f.market_cap,
                m.close as current_price
            FROM fundamentals f
            LEFT JOIN market_data m 
                ON f.symbol = m.symbol 
                AND m.date = (SELECT MAX(date) FROM market_data WHERE symbol = f.symbol)
            WHERE f.pe_ratio < {max_pe}
            AND f.pe_ratio > 0
            ORDER BY f.pe_ratio ASC
        """
        
        return self.conn.execute(query).df()
    
    def get_portfolio_stats(self, trades_df: pd.DataFrame) -> Dict:
        """Calculate portfolio statistics"""
        self.conn.register('temp_trades', trades_df)
        
        stats = self.conn.execute("""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                SUM(pnl) / COUNT(*) * STDDEV(pnl) as sharpe_ratio,
                MAX(pnl) as max_win,
                MIN(pnl) as max_loss,
                AVG(return_pct) as avg_return_pct
            FROM temp_trades
        """).fetchall()
        
        self.conn.unregister('temp_trades')
        
        if stats and stats[0]:
            cols = ['total_trades', 'winning_trades', 'losing_trades', 'total_pnl', 
                   'avg_pnl', 'sharpe_ratio', 'max_win', 'max_loss', 'avg_return_pct']
            return dict(zip(cols, stats[0]))
        return {}
    
    def get_sector_performance(self) -> pd.DataFrame:
        """Analyze performance by sector (requires sector mapping)"""
        # This is a placeholder - would need sector classification data
        pass
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("DuckDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    with DuckDBAnalytics() as db:
        # Test insertion
        sample_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'symbol': ['AAPL'] * 10,
            'open': [150] * 10,
            'high': [152] * 10,
            'low': [149] * 10,
            'close': range(150, 160),
            'volume': [1000000] * 10,
            'adj_close': range(150, 160)
        })
        
        db.insert_market_data(sample_data)
        
        # Test queries
        perf = db.get_stock_performance('AAPL')
        print("Stock Performance:")
        print(perf)
