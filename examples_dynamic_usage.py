"""Praktische Beispiele für die dynamische Verwendung von add_item()"""

import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent / "src"))

from watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory, WatchlistItem


def example_1_loop_through_symbols():
    """Beispiel 1: Symbole aus einer Liste dynamisch hinzufügen"""
    print("\n" + "="*70)
    print("BEISPIEL 1: Dynamische Schleife über Symbole")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example1.db"
        watchlist = Watchlist(name="Tech Stocks", db_path=str(db_path))
        
        # Liste von Tech-Aktien
        tech_stocks = [
            ("AAPL", "Apple Inc."),
            ("MSFT", "Microsoft Corporation"),
            ("GOOGL", "Alphabet Inc."),
            ("META", "Meta Platforms Inc."),
            ("NVDA", "NVIDIA Corporation"),
            ("TSLA", "Tesla Inc."),
        ]
        
        # Dynamisch hinzufügen
        for symbol, name in tech_stocks:
            item = watchlist.add_item(
                symbol,  # Dynamisch!
                name=name,
                asset_class=AssetClass.STOCK,
                category=WatchlistCategory.GROWTH
            )
            print(f"✓ Hinzugefügt: {item.symbol} - {item.name}")
        
        print(f"\n📊 Total: {len(watchlist.get_all())} Aktien in der Watchlist")


def example_2_user_input_simulation():
    """Beispiel 2: Benutzer-Input simulieren"""
    print("\n" + "="*70)
    print("BEISPIEL 2: Benutzer-Input Simulation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example2.db"
        watchlist = Watchlist(name="User Portfolio", db_path=str(db_path))
        
        # Simuliere Benutzer-Eingaben
        user_inputs = [
            {"symbol": "AMZN", "name": "Amazon", "target": 180.0},
            {"symbol": "NFLX", "name": "Netflix", "target": 500.0},
            {"symbol": "DIS", "name": "Disney", "target": 120.0},
        ]
        
        for user_input in user_inputs:
            symbol = user_input["symbol"]
            name = user_input["name"]
            target = user_input["target"]
            
            item = watchlist.add_item(
                symbol=symbol,  # Dynamisch vom "Benutzer"
                name=name,
                asset_class=AssetClass.STOCK,
                category=WatchlistCategory.VALUE,
                target_price=target
            )
            print(f"✓ Benutzer fügte hinzu: {item.symbol} (Ziel: ${item.target_price})")
        
        print(f"\n📊 Total: {len(watchlist.get_all())} Aktien")


def example_3_mixed_asset_classes():
    """Beispiel 3: Verschiedene Asset-Klassen dynamisch"""
    print("\n" + "="*70)
    print("BEISPIEL 3: Gemischtes Portfolio (Aktien, Crypto, Bonds)")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example3.db"
        watchlist = Watchlist(name="Diversified Portfolio", db_path=str(db_path))
        
        # Portfolio-Daten mit verschiedenen Asset-Klassen
        portfolio = [
            # Aktien
            ("AAPL", "Apple Inc.", AssetClass.STOCK, WatchlistCategory.GROWTH),
            ("JNJ", "Johnson & Johnson", AssetClass.STOCK, WatchlistCategory.DIVIDEND),
            
            # Kryptowährungen
            ("BTC-USD", "Bitcoin", AssetClass.CRYPTO, WatchlistCategory.MOMENTUM),
            ("ETH-USD", "Ethereum", AssetClass.CRYPTO, WatchlistCategory.MOMENTUM),
            
            # Bonds
            ("AGG", "Core Bond ETF", AssetClass.BOND, WatchlistCategory.INCOME),
            ("TLT", "Treasury Bond ETF", AssetClass.BOND, WatchlistCategory.INCOME),
            
            # Forex
            ("EUR/USD", "Euro/Dollar", AssetClass.FOREX, WatchlistCategory.TECHNICAL),
        ]
        
        for symbol, name, asset_class, category in portfolio:
            item = watchlist.add_item(
                symbol,  # Vollständig dynamisch!
                name=name,
                asset_class=asset_class,
                category=category
            )
            print(f"✓ {asset_class.value:8} | {item.symbol:12} | {item.name}")
        
        # Zusammenfassung
        summary = watchlist.get_summary()
        print(f"\n📊 Portfolio-Zusammenfassung:")
        print(f"   Total Items: {summary['total_items']}")
        for asset_class, count in summary['asset_classes'].items():
            print(f"   - {asset_class}: {count}")


def example_4_conditional_adding():
    """Beispiel 4: Bedingt Items hinzufügen"""
    print("\n" + "="*70)
    print("BEISPIEL 4: Bedingte Logik beim Hinzufügen")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example4.db"
        watchlist = Watchlist(name="Filtered Stocks", db_path=str(db_path))
        
        # Simulierte Marktdaten
        market_data = [
            {"symbol": "AAPL", "name": "Apple", "price": 180.0, "volume": 50000000},
            {"symbol": "MSFT", "name": "Microsoft", "price": 380.0, "volume": 30000000},
            {"symbol": "SMALL", "name": "Small Cap", "price": 10.0, "volume": 100000},
            {"symbol": "GOOGL", "name": "Google", "price": 140.0, "volume": 25000000},
        ]
        
        # Nur Aktien mit hohem Volumen hinzufügen
        MIN_VOLUME = 20000000
        
        for data in market_data:
            if data["volume"] >= MIN_VOLUME:
                item = watchlist.add_item(
                    symbol=data["symbol"],  # Dynamisch basierend auf Bedingung
                    name=data["name"],
                    asset_class=AssetClass.STOCK,
                    category=WatchlistCategory.MOMENTUM
                )
                print(f"✓ Hinzugefügt: {item.symbol} (Volume: {data['volume']:,})")
            else:
                print(f"✗ Übersprungen: {data['symbol']} (Volume zu niedrig: {data['volume']:,})")
        
        print(f"\n📊 {len(watchlist.get_all())} von {len(market_data)} Aktien hinzugefügt")


def example_5_batch_with_error_handling():
    """Beispiel 5: Batch-Import mit Fehlerbehandlung"""
    print("\n" + "="*70)
    print("BEISPIEL 5: Batch-Import mit Fehlerbehandlung")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example5.db"
        watchlist = Watchlist(name="Batch Import", db_path=str(db_path))
        
        # Simulierte Import-Daten (einige könnten fehlerhaft sein)
        import_data = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corp."},
            {"symbol": "", "name": "Invalid Empty"},  # Fehler: leeres Symbol
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
        ]
        
        success_count = 0
        error_count = 0
        
        for data in import_data:
            try:
                symbol = data["symbol"]
                if not symbol:  # Validierung
                    raise ValueError("Symbol darf nicht leer sein")
                
                item = watchlist.add_item(
                    symbol=symbol,  # Dynamisch mit Validierung
                    name=data["name"],
                    asset_class=AssetClass.STOCK,
                    category=WatchlistCategory.CUSTOM
                )
                print(f"✓ Erfolgreich: {item.symbol}")
                success_count += 1
                
            except Exception as e:
                print(f"✗ Fehler bei '{data.get('symbol', 'N/A')}': {e}")
                error_count += 1
        
        print(f"\n📊 Ergebnis: {success_count} erfolgreich, {error_count} Fehler")


def example_6_dictionary_mapping():
    """Beispiel 6: Dictionary-basierte Konfiguration"""
    print("\n" + "="*70)
    print("BEISPIEL 6: Dictionary-basierte Konfiguration")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example6.db"
        watchlist = Watchlist(name="Config-based", db_path=str(db_path))
        
        # Konfiguration als Dictionary
        config = {
            "growth_stocks": {
                "symbols": ["AAPL", "MSFT", "GOOGL"],
                "asset_class": AssetClass.STOCK,
                "category": WatchlistCategory.GROWTH
            },
            "dividend_stocks": {
                "symbols": ["JNJ", "PG", "KO"],
                "asset_class": AssetClass.STOCK,
                "category": WatchlistCategory.DIVIDEND
            },
            "crypto": {
                "symbols": ["BTC-USD", "ETH-USD"],
                "asset_class": AssetClass.CRYPTO,
                "category": WatchlistCategory.MOMENTUM
            }
        }
        
        # Dynamisch aus Konfiguration hinzufügen
        for group_name, group_config in config.items():
            print(f"\n📁 Gruppe: {group_name}")
            for symbol in group_config["symbols"]:
                item = watchlist.add_item(
                    symbol=symbol,  # Dynamisch aus Config
                    name=f"{symbol} Asset",
                    asset_class=group_config["asset_class"],
                    category=group_config["category"]
                )
                print(f"   ✓ {item.symbol}")
        
        print(f"\n📊 Total: {len(watchlist.get_all())} Items aus Konfiguration")


def example_7_watchlist_item_objects():
    """Beispiel 7: Mit WatchlistItem-Objekten arbeiten"""
    print("\n" + "="*70)
    print("BEISPIEL 7: WatchlistItem-Objekte verwenden")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example7.db"
        watchlist = Watchlist(name="Object-based", db_path=str(db_path))
        
        # Erstelle Items vorab
        items_to_add = []
        
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        for i, symbol in enumerate(symbols):
            item = WatchlistItem(
                symbol=symbol,  # Dynamisch!
                name=f"{symbol} Company",
                asset_class=AssetClass.STOCK,
                category=WatchlistCategory.GROWTH,
                target_price=100.0 + (i * 50),
                tags=[f"Tag{i}", "Dynamic"]
            )
            items_to_add.append(item)
        
        # Füge alle Items hinzu
        for item in items_to_add:
            added = watchlist.add_item(item)  # Objekt übergeben
            print(f"✓ {added.symbol} | Target: ${added.target_price} | Tags: {added.tags}")
        
        print(f"\n📊 {len(watchlist.get_all())} Items als Objekte hinzugefügt")


def example_8_real_world_scenario():
    """Beispiel 8: Realistisches Szenario - Watchlist aus API-Daten"""
    print("\n" + "="*70)
    print("BEISPIEL 8: Realistisches Szenario - API-ähnliche Daten")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "example8.db"
        watchlist = Watchlist(name="API Import", db_path=str(db_path))
        
        # Simuliere API-Response
        api_response = {
            "trending": [
                {"ticker": "AAPL", "company": "Apple Inc.", "price": 180.5, "change": 2.5},
                {"ticker": "NVDA", "company": "NVIDIA Corp.", "price": 880.0, "change": 15.2},
                {"ticker": "TSLA", "company": "Tesla Inc.", "price": 245.0, "change": -3.1},
            ],
            "timestamp": "2026-01-19T10:00:00Z"
        }
        
        print(f"📡 API-Daten empfangen: {api_response['timestamp']}")
        print(f"📈 {len(api_response['trending'])} Trending Stocks\n")
        
        for stock in api_response["trending"]:
            # Bestimme Kategorie basierend auf Preisänderung
            category = (WatchlistCategory.MOMENTUM if stock["change"] > 0 
                       else WatchlistCategory.VALUE)
            
            item = watchlist.add_item(
                symbol=stock["ticker"],  # Dynamisch aus API
                name=stock["company"],
                asset_class=AssetClass.STOCK,
                category=category,
                target_price=stock["price"] * 1.1,  # 10% über aktuellem Preis
                notes=f"API Import: {stock['change']:+.2f}% change"
            )
            
            emoji = "📈" if stock["change"] > 0 else "📉"
            print(f"{emoji} {item.symbol:6} | ${stock['price']:7.2f} | "
                  f"Change: {stock['change']:+6.2f}% | Target: ${item.target_price:.2f}")
        
        print(f"\n📊 {len(watchlist.get_all())} Stocks aus API importiert")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRAKTISCHE BEISPIELE - DYNAMISCHE ADD_ITEM VERWENDUNG")
    print("="*70)
    
    # Führe alle Beispiele aus
    example_1_loop_through_symbols()
    example_2_user_input_simulation()
    example_3_mixed_asset_classes()
    example_4_conditional_adding()
    example_5_batch_with_error_handling()
    example_6_dictionary_mapping()
    example_7_watchlist_item_objects()
    example_8_real_world_scenario()
    
    print("\n" + "="*70)
    print("✅ ALLE BEISPIELE ERFOLGREICH AUSGEFÜHRT!")
    print("="*70)
    print("\n💡 Die add_item() Methode ist vollständig dynamisch und")
    print("   funktioniert mit beliebigen Symbolen und Datenquellen!")
