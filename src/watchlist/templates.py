"""Pre-populated watchlist templates"""

from .watchlist import Watchlist, AssetClass, WatchlistCategory


def create_tech_momentum_watchlist() -> Watchlist:
    """Create tech momentum watchlist"""
    watchlist = Watchlist(name="Tech Momentum")
    
    tech_stocks = [
        ("AAPL", "Apple Inc.", 150.0, 160.0, 140.0, "Strong momentum, high volume"),
        ("MSFT", "Microsoft Corp.", 380.0, 400.0, 360.0, "AI leadership, growth"),
        ("NVDA", "NVIDIA Corp.", 875.0, 950.0, 800.0, "AI chip leader"),
        ("GOOGL", "Alphabet Inc.", 140.0, 155.0, 130.0, "Tech diversification"),
        ("META", "Meta Platforms", 475.0, 520.0, 440.0, "AI investments, recovery"),
        ("TSLA", "Tesla Inc.", 242.0, 280.0, 220.0, "EV leader, innovation"),
        ("AMD", "Advanced Micro Devices", 180.0, 200.0, 160.0, "Semiconductor play"),
        ("AVGO", "Broadcom Inc.", 180.0, 200.0, 165.0, "Infrastructure chip"),
    ]
    
    for symbol, name, current, target, stop, notes in tech_stocks:
        watchlist.add_item(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.STOCK,
            category=WatchlistCategory.MOMENTUM,
            target_price=target,
            stop_loss=stop,
            notes=notes,
            tags=["Tech", "Large-Cap", "Momentum"]
        )
    
    return watchlist


def create_dividend_watchlist() -> Watchlist:
    """Create dividend growth watchlist"""
    watchlist = Watchlist(name="Dividend Growth")
    
    dividend_stocks = [
        ("JNJ", "Johnson & Johnson", 160.0, 175.0, 150.0, "Dividend aristocrat"),
        ("PG", "Procter & Gamble", 170.0, 185.0, 160.0, "Consumer staples, dividends"),
        ("KO", "The Coca-Cola Company", 61.0, 68.0, 57.0, "Beverage leader, yield"),
        ("MCD", "McDonald's Corp.", 295.0, 320.0, 280.0, "Franchising model"),
        ("PEP", "PepsiCo Inc.", 188.0, 205.0, 175.0, "Diversified beverage/snacks"),
        ("CSCO", "Cisco Systems", 52.0, 58.0, 48.0, "Networking, dividends"),
        ("INTC", "Intel Corp.", 45.0, 55.0, 40.0, "Semiconductor, dividend recovery"),
        ("VZ", "Verizon Communications", 42.0, 47.0, 39.0, "Telecom, stable yield"),
    ]
    
    for symbol, name, current, target, stop, notes in dividend_stocks:
        watchlist.add_item(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.STOCK,
            category=WatchlistCategory.DIVIDEND,
            target_price=target,
            stop_loss=stop,
            notes=notes,
            tags=["Dividend", "Income", "Stable"]
        )
    
    return watchlist


def create_value_watchlist() -> Watchlist:
    """Create value investing watchlist"""
    watchlist = Watchlist(name="Value Picks")
    
    value_stocks = [
        ("JPM", "JPMorgan Chase", 195.0, 215.0, 180.0, "Banking leader, valuation"),
        ("BAC", "Bank of America", 34.0, 39.0, 30.0, "Banking sector value"),
        ("F", "Ford Motor", 12.0, 14.0, 10.0, "Auto industry recovery"),
        ("GE", "General Electric", 180.0, 200.0, 165.0, "Industrial conglomerate"),
        ("XOM", "ExxonMobil", 110.0, 125.0, 100.0, "Energy sector value"),
        ("CVX", "Chevron Corp", 155.0, 170.0, 145.0, "Oil & gas producer"),
        ("BTU", "Peabody Energy", 18.0, 22.0, 15.0, "Coal producer value"),
        ("IBM", "IBM Corp", 195.0, 215.0, 180.0, "Enterprise software/services"),
    ]
    
    for symbol, name, current, target, stop, notes in value_stocks:
        watchlist.add_item(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.STOCK,
            category=WatchlistCategory.VALUE,
            target_price=target,
            stop_loss=stop,
            notes=notes,
            tags=["Value", "Low-P/E", "Cyclical"]
        )
    
    return watchlist


def create_growth_watchlist() -> Watchlist:
    """Create growth-focused watchlist"""
    watchlist = Watchlist(name="Growth Stories")
    
    growth_stocks = [
        ("ASML", "ASML Holding", 640.0, 720.0, 600.0, "Semiconductor equipment leader"),
        ("AXON", "Axon Enterprise", 285.0, 320.0, 260.0, "Police tech/cloud growth"),
        ("CRM", "Salesforce Inc.", 298.0, 330.0, 275.0, "Cloud CRM leader"),
        ("NOW", "ServiceNow Inc.", 805.0, 900.0, 750.0, "Enterprise cloud platform"),
        ("ADBE", "Adobe Inc.", 515.0, 580.0, 480.0, "Creative cloud platform"),
        ("OKTA", "Okta Inc.", 104.0, 125.0, 95.0, "Identity cloud"),
        ("PAYC", "Paylocity Holding", 245.0, 280.0, 220.0, "HR tech growth"),
        ("APP", "AppLovin Corp.", 150.0, 175.0, 135.0, "Mobile software platform"),
    ]
    
    for symbol, name, current, target, stop, notes in growth_stocks:
        watchlist.add_item(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.STOCK,
            category=WatchlistCategory.GROWTH,
            target_price=target,
            stop_loss=stop,
            notes=notes,
            tags=["Growth", "SaaS", "Cloud", "High-Growth"]
        )
    
    return watchlist


def create_etf_watchlist() -> Watchlist:
    """Create ETF watchlist"""
    watchlist = Watchlist(name="ETF Portfolio")
    
    etfs = [
        ("SPY", "SPDR S&P 500 ETF Trust", 520.0, 560.0, 490.0, "US market broad exposure"),
        ("QQQ", "Invesco QQQ Trust", 445.0, 480.0, 410.0, "Nasdaq 100 growth"),
        ("IWM", "iShares Russell 2000 ETF", 210.0, 235.0, 190.0, "Small-cap growth"),
        ("VTI", "Vanguard Total Stock Market", 255.0, 280.0, 235.0, "Total US market"),
        ("AGG", "iShares Core US Aggregate Bond", 95.0, 100.0, 92.0, "Bond portfolio"),
        ("GLD", "SPDR Gold Shares", 195.0, 210.0, 180.0, "Gold commodity"),
        ("TLT", "iShares 20+ Year Treasury", 92.0, 98.0, 87.0, "Long-term bonds"),
        ("VGK", "Vanguard FTSE Europe ETF", 65.0, 72.0, 60.0, "European exposure"),
    ]
    
    for symbol, name, current, target, stop, notes in etfs:
        watchlist.add_item(
            symbol=symbol,
            name=name,
            asset_class=AssetClass.ETF,
            category=WatchlistCategory.TECHNICAL,
            target_price=target,
            stop_loss=stop,
            notes=notes,
            tags=["ETF", "Index", "Diversification"]
        )
    
    return watchlist


def populate_default_watchlists() -> dict:
    """Create and populate all default watchlists"""
    watchlists = {
        "Tech Momentum": create_tech_momentum_watchlist(),
        "Dividend Growth": create_dividend_watchlist(),
        "Value Picks": create_value_watchlist(),
        "Growth Stories": create_growth_watchlist(),
        "ETF Portfolio": create_etf_watchlist(),
    }
    return watchlists
