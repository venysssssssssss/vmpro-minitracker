# filepath: /home/synev1/dev/vmpro/app/stock-tracker/src/services/stock_data_service.py
from datetime import datetime
from typing import Dict, List, Optional

import requests_cache
import yfinance as yf

from interfaces.data_provider import DataProvider
from models.stock import Stock

# Cache para evitar muitas requisições
requests_cache.install_cache('stock_cache', expire_after=300)  # 5 minutos


class YahooFinanceProvider(DataProvider):
    """Implementação usando Yahoo Finance API real com yfinance"""

    def __init__(self):
        pass

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma ação específica usando yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='2d')

            if hist.empty:
                return None

            current_price = float(hist['Close'].iloc[-1])
            previous_close = (
                float(hist['Close'].iloc[-2])
                if len(hist) > 1
                else current_price
            )
            current_volume = (
                int(hist['Volume'].iloc[-1])
                if not hist['Volume'].empty
                else None
            )

            return {
                'symbol': symbol.upper(),
                'name': info.get(
                    'longName', info.get('shortName', symbol.upper())
                ),
                'price': current_price,
                'previous_close': previous_close,
                'market_cap': info.get('marketCap'),
                'volume': current_volume,
                'last_updated': datetime.now(),
            }

        except Exception as e:
            print(f'Erro ao buscar dados para {symbol}: {e}')
            return None

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca dados de múltiplas ações"""
        result = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data:
                result[symbol.upper()] = data
        return result

    def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """Busca ações em alta usando dados reais do mercado"""
        try:
            popular_stocks = [
                'AAPL',
                'MSFT',
                'GOOGL',
                'AMZN',
                'TSLA',
                'NVDA',
                'META',
                'NFLX',
                'V',
                'JPM',
            ]
            stocks_data = []

            for symbol in popular_stocks[:limit]:
                try:
                    data = self.get_stock_data(symbol)
                    if data and data['previous_close'] > 0:
                        change_percent = (
                            (data['price'] - data['previous_close'])
                            / data['previous_close']
                        ) * 100
                        data['change_percent'] = change_percent
                        stocks_data.append(data)
                except Exception as e:
                    print(f'Erro ao buscar {symbol}: {e}')
                    continue

            stocks_data.sort(
                key=lambda x: x.get('change_percent', 0), reverse=True
            )
            return stocks_data[:limit]

        except Exception as e:
            print(f'Erro ao buscar ações em alta: {e}')
            return []


class MockStockProvider(DataProvider):
    """Implementação mock para testes e desenvolvimento"""

    def __init__(self):
        import random

        base_time = datetime.now()

        self.mock_data = {
            'AAPL': {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'price': round(175.50 + random.uniform(-5, 5), 2),
                'previous_close': 172.30,
                'market_cap': 2800000000000,
                'volume': random.randint(45000000, 55000000),
                'last_updated': base_time,
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'price': round(2450.75 + random.uniform(-50, 50), 2),
                'previous_close': 2425.60,
                'market_cap': 1600000000000,
                'volume': random.randint(20000000, 30000000),
                'last_updated': base_time,
            },
            'MSFT': {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'price': round(335.20 + random.uniform(-10, 10), 2),
                'previous_close': 330.15,
                'market_cap': 2500000000000,
                'volume': random.randint(30000000, 40000000),
                'last_updated': base_time,
            },
        }

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Retorna dados mock de uma ação"""
        return self.mock_data.get(symbol.upper())

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Retorna dados mock de múltiplas ações"""
        result = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data:
                result[symbol.upper()] = data
        return result

    def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """Retorna ações mock em alta ordenadas por performance"""
        stocks = list(self.mock_data.values())
        stocks.sort(
            key=lambda x: (
                (x['price'] - x['previous_close']) / x['previous_close'] * 100
            ),
            reverse=True,
        )
        return stocks[:limit]
