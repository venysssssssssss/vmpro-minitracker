from datetime import datetime
from typing import Dict, List, Optional

import requests
import requests_cache
from pycoingecko import CoinGeckoAPI

from interfaces.data_provider import CryptoDataProvider
from models.stock import Crypto

# Cache para evitar muitas requisições
requests_cache.install_cache('crypto_cache', expire_after=300)  # 5 minutos


class CoinGeckoProvider(CryptoDataProvider):
    """Implementação usando CoinGecko API real com pycoingecko"""

    def __init__(self):
        self.cg = CoinGeckoAPI()
        # Mapping de símbolos para IDs do CoinGecko
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
        }

    def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma criptomoeda específica"""
        try:
            crypto_id = self.symbol_to_id.get(symbol.upper())
            if not crypto_id:
                # Tentar buscar pelo símbolo
                search_results = self.cg.search(query=symbol)
                if search_results['coins']:
                    crypto_id = search_results['coins'][0]['id']
                else:
                    return None

            # Buscar dados atuais
            data = self.cg.get_coin_by_id(
                id=crypto_id,
                localization=False,
                tickers=False,
                market_data=True,
                community_data=False,
                developer_data=False,
                sparkline=False,
            )

            market_data = data.get('market_data', {})
            current_price = market_data.get('current_price', {}).get('usd', 0)
            price_change_24h = market_data.get(
                'price_change_percentage_24h', 0
            )

            # Calcular preço anterior baseado na mudança de 24h
            if price_change_24h != 0:
                previous_price = current_price / (1 + (price_change_24h / 100))
            else:
                previous_price = current_price

            return {
                'symbol': symbol.upper(),
                'name': data.get('name', symbol),
                'price': current_price,
                'previous_close': previous_price,
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'volume_24h': market_data.get('total_volume', {}).get('usd'),
                'change_percent_24h': price_change_24h,
                'last_updated': datetime.now(),
            }

        except Exception as e:
            print(f'Erro ao buscar dados para {symbol}: {e}')
            return None

    def get_multiple_cryptos(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca dados de múltiplas criptomoedas"""
        result = {}
        for symbol in symbols:
            data = self.get_crypto_data(symbol)
            if data:
                result[symbol.upper()] = data
        return result

    def get_trending_cryptos(self, limit: int = 10) -> List[Dict]:
        """Busca criptomoedas em alta usando dados reais"""
        try:
            # Buscar criptos por market cap com dados de mudança
            coins = self.cg.get_coins_markets(
                vs_currency='usd',
                order='percent_change_24h_desc',
                per_page=limit,
                page=1,
                sparkline=False,
                price_change_percentage='24h',
            )

            result = []
            for coin in coins:
                current_price = coin.get('current_price', 0)
                price_change_24h = coin.get('price_change_percentage_24h', 0)

                if price_change_24h != 0:
                    previous_price = current_price / (
                        1 + (price_change_24h / 100)
                    )
                else:
                    previous_price = current_price

                result.append(
                    {
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name', ''),
                        'price': current_price,
                        'previous_close': previous_price,
                        'market_cap': coin.get('market_cap'),
                        'volume_24h': coin.get('total_volume'),
                        'change_percent_24h': price_change_24h,
                        'last_updated': datetime.now(),
                    }
                )

            return result

        except Exception as e:
            print(f'Erro ao buscar criptos em alta: {e}')
            return []


class MockCryptoProvider(CryptoDataProvider):
    """Implementação mock para testes e desenvolvimento"""

    def __init__(self):
        import random

        base_time = datetime.now()

        self.mock_data = {
            'BTC': {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'price': round(45000.50 + random.uniform(-2000, 2000), 2),
                'previous_close': 43500.20,
                'market_cap': 850000000000,
                'volume_24h': random.randint(20000000000, 30000000000),
                'change_percent_24h': round(random.uniform(-5, 8), 2),
                'last_updated': base_time,
            },
            'ETH': {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'price': round(3200.75 + random.uniform(-200, 200), 2),
                'previous_close': 3150.30,
                'market_cap': 380000000000,
                'volume_24h': random.randint(10000000000, 20000000000),
                'change_percent_24h': round(random.uniform(-3, 6), 2),
                'last_updated': base_time,
            },
            'ADA': {
                'symbol': 'ADA',
                'name': 'Cardano',
                'price': round(1.25 + random.uniform(-0.2, 0.2), 2),
                'previous_close': 1.18,
                'market_cap': 40000000000,
                'volume_24h': random.randint(1000000000, 3000000000),
                'change_percent_24h': round(random.uniform(-2, 10), 2),
                'last_updated': base_time,
            },
            'DOT': {
                'symbol': 'DOT',
                'name': 'Polkadot',
                'price': round(25.30 + random.uniform(-3, 3), 2),
                'previous_close': 24.50,
                'market_cap': 25000000000,
                'volume_24h': random.randint(500000000, 1500000000),
                'change_percent_24h': round(random.uniform(-1, 7), 2),
                'last_updated': base_time,
            },
            'LINK': {
                'symbol': 'LINK',
                'name': 'Chainlink',
                'price': round(18.75 + random.uniform(-2, 2), 2),
                'previous_close': 17.90,
                'market_cap': 9000000000,
                'volume_24h': random.randint(300000000, 800000000),
                'change_percent_24h': round(random.uniform(0, 8), 2),
                'last_updated': base_time,
            },
        }

    def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Retorna dados mock de uma criptomoeda"""
        return self.mock_data.get(symbol.upper())

    def get_multiple_cryptos(self, symbols: List[str]) -> Dict[str, Dict]:
        """Retorna dados mock de múltiplas criptomoedas"""
        result = {}
        for symbol in symbols:
            data = self.get_crypto_data(symbol)
            if data:
                result[symbol.upper()] = data
        return result

    def get_trending_cryptos(self, limit: int = 10) -> List[Dict]:
        """Retorna criptos mock em alta ordenadas por performance"""
        cryptos = list(self.mock_data.values())

        # Ordenar por mudança percentual
        cryptos.sort(key=lambda x: x['change_percent_24h'], reverse=True)

        return cryptos[:limit]
