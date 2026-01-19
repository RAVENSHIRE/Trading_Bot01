"""Test dynamic add_item functionality with various symbols and call patterns"""

import sys
from pathlib import Path
from datetime import datetime
import tempfile

sys.path.insert(0, str(Path(__file__).parent / "src"))

from watchlist.watchlist import Watchlist, AssetClass, WatchlistCategory, WatchlistItem


def test_dynamic_symbols():
    """Test add_item with various dynamic symbols"""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        wl = Watchlist(name="Dynamic Test", db_path=str(db_path))
        
        # Test 1: Verschiedene Aktien-Symbole als Positionsargument
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META"]
        
        for symbol in symbols:
            item = wl.add_item(
                symbol,
                name=f"{symbol} Company",
                asset_class=AssetClass.STOCK,
                category=WatchlistCategory.GROWTH
            )
            print(f"✓ Added {symbol} as positional argument: {item.symbol}")
            assert item.symbol == symbol
        
        print(f"\n✓ Total items after positional args: {len(wl.get_all())}")
        assert len(wl.get_all()) == 7
        
        # Test 2: Verschiedene Symbole als Keyword-Argument
        crypto_symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"]
        
        for symbol in crypto_symbols:
            item = wl.add_item(
                symbol=symbol,
                name=f"{symbol} Crypto",
                asset_class=AssetClass.CRYPTO,
                category=WatchlistCategory.MOMENTUM
            )
            print(f"✓ Added {symbol} as keyword argument: {item.symbol}")
            assert item.symbol == symbol
        
        print(f"\n✓ Total items after keyword args: {len(wl.get_all())}")
        assert len(wl.get_all()) == 11
        
        # Test 3: WatchlistItem-Objekte mit verschiedenen Symbolen
        bond_symbols = ["AGG", "BND", "TLT", "IEF"]
        
        for symbol in bond_symbols:
            item = WatchlistItem(
                symbol=symbol,
                name=f"{symbol} Bond ETF",
                asset_class=AssetClass.BOND,
                category=WatchlistCategory.INCOME
            )
            added_item = wl.add_item(item)
            print(f"✓ Added {symbol} as WatchlistItem object: {added_item.symbol}")
            assert added_item.symbol == symbol
        
        print(f"\n✓ Total items after WatchlistItem objects: {len(wl.get_all())}")
        assert len(wl.get_all()) == 15
        
        # Test 4: Forex-Paare mit Sonderzeichen
        forex_symbols = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
        
        for symbol in forex_symbols:
            item = wl.add_item(
                symbol=symbol,
                name=f"{symbol} Forex Pair",
                asset_class=AssetClass.FOREX,
                category=WatchlistCategory.TECHNICAL
            )
            print(f"✓ Added {symbol} as forex pair: {item.symbol}")
            assert item.symbol == symbol
        
        print(f"\n✓ Total items after forex pairs: {len(wl.get_all())}")
        assert len(wl.get_all()) == 19
        
        # Test 5: Gemischte Aufrufvarianten in einer Schleife
        mixed_data = [
            ("SPOT", "Spotify", AssetClass.STOCK, WatchlistCategory.GROWTH),
            ("DIS", "Disney", AssetClass.STOCK, WatchlistCategory.VALUE),
            ("NKE", "Nike", AssetClass.STOCK, WatchlistCategory.MOMENTUM),
        ]
        
        for i, (symbol, name, asset_class, category) in enumerate(mixed_data):
            if i % 2 == 0:
                # Positionsargument
                item = wl.add_item(symbol, name=name, asset_class=asset_class, category=category)
                print(f"✓ Added {symbol} (positional, iteration {i}): {item.symbol}")
            else:
                # Keyword-Argument
                item = wl.add_item(symbol=symbol, name=name, asset_class=asset_class, category=category)
                print(f"✓ Added {symbol} (keyword, iteration {i}): {item.symbol}")
            
            assert item.symbol == symbol
        
        print(f"\n✓ Final total items: {len(wl.get_all())}")
        assert len(wl.get_all()) == 22
        
        # Test 6: Überprüfung der gespeicherten Daten
        print("\n=== Zusammenfassung ===")
        summary = wl.get_summary()
        print(f"Total Items: {summary['total_items']}")
        print(f"Asset Classes: {summary['asset_classes']}")
        print(f"Categories: {summary['categories']}")
        
        # Verifiziere spezifische Symbole
        test_symbols = ["AAPL", "BTC-USD", "AGG", "EUR/USD", "SPOT"]
        for symbol in test_symbols:
            item = wl.get_item(symbol)
            assert item is not None, f"Symbol {symbol} should exist"
            print(f"✓ Verified {symbol}: {item.name}")
        
        print("\n✅ Alle dynamischen Tests erfolgreich!")


def test_edge_cases():
    """Test edge cases and special characters"""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_edge.db"
        wl = Watchlist(name="Edge Cases", db_path=str(db_path))
        
        # Symbole mit Sonderzeichen
        special_symbols = [
            "BRK.B",      # Punkt
            "BF-B",       # Bindestrich
            "^GSPC",      # Caret (S&P 500 Index)
            "ES=F",       # Futures
            "GC=F",       # Gold Futures
        ]
        
        for symbol in special_symbols:
            item = wl.add_item(
                symbol=symbol,
                name=f"Special: {symbol}",
                asset_class=AssetClass.STOCK,
                category=WatchlistCategory.CUSTOM
            )
            print(f"✓ Added special symbol {symbol}: {item.symbol}")
            assert item.symbol == symbol
        
        print(f"\n✓ All {len(special_symbols)} special symbols added successfully")
        print("✅ Edge cases Test erfolgreich!")


if __name__ == "__main__":
    print("=" * 70)
    print("DYNAMISCHE ADD_ITEM TESTS")
    print("=" * 70)
    print()
    
    try:
        test_dynamic_symbols()
        print("\n" + "=" * 70)
        test_edge_cases()
        print("\n" + "=" * 70)
        print("\n🎉 ALLE TESTS ERFOLGREICH ABGESCHLOSSEN!")
        print("Die add_item() Methode funktioniert vollständig dynamisch!")
    except AssertionError as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}")
        raise
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        raise
