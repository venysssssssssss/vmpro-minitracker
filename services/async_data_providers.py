"""
Provedores de Dados Assíncronos
Implementações otimizadas para APIs Yahoo Finance e CoinGecko
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import yfinance as yf
from pycoingecko import CoinGeckoAPI

from utils.config import Config


class AsyncDataProvider:
    """Classe base para provedores de dados assíncronos"""

    def __init__(self, max_concurrent: int = 10, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Estatísticas
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0.0

    async def initialize(self):
        """Inicializa a sessão HTTP"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Mini-Tracker/2.0 (Financial Data Aggregator)',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate',
                },
            )

    async def close(self):
        """Fecha a sessão HTTP"""
        if self.session:
            await self.session.close()
            self.session = None

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do provedor"""
        return {
            'status': 'healthy' if self.session else 'not_initialized',
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': (self.error_count / max(1, self.request_count))
            * 100,
            'avg_response_time': self.total_time / max(1, self.request_count),
        }


class AsyncYahooProvider(AsyncDataProvider):
    """Provedor assíncrono para Yahoo Finance com otimizações"""

    def __init__(self):
        super().__init__(
            max_concurrent=Config.MAX_CONCURRENT_REQUESTS,
            timeout=Config.REQUEST_TIMEOUT,
        )
        self.base_url = 'https://query1.finance.yahoo.com/v8/finance/chart'

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma ação específica"""
        async with self.semaphore:
            start_time = time.time()

            try:
                await self.initialize()

                # Usar yfinance de forma síncrona em thread separada
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None, self._fetch_stock_sync, symbol
                )

                self.request_count += 1
                self.total_time += time.time() - start_time

                return data

            except Exception as e:
                self.error_count += 1
                print(f'⚠️ Erro ao buscar {symbol}: {e}')
                return None

    def _fetch_stock_sync(self, symbol: str) -> Optional[Dict]:
        """Busca dados de ação de forma síncrona (para executar em thread)"""
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
            print(f'Erro no _fetch_stock_sync para {symbol}: {e}')
            return None

    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca múltiplas ações de forma concorrente"""
        tasks = []

        for symbol in symbols:
            task = asyncio.create_task(self.get_stock_data(symbol))
            tasks.append((symbol, task))

        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for (symbol, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                print(f'⚠️ Erro ao buscar {symbol}: {result}')
            elif result:
                results[symbol.upper()] = result

        return results

    async def get_trending_stocks(self, symbols: List[str]) -> List[Dict]:
        """Busca ações populares e calcula trending"""
        stocks_data = await self.get_multiple_stocks(symbols)

        # Converter para lista e calcular mudanças percentuais
        trending_list = []

        for symbol, data in stocks_data.items():
            if data and data.get('previous_close', 0) > 0:
                change_percent = (
                    (data['price'] - data['previous_close'])
                    / data['previous_close']
                ) * 100
                data['change_percent'] = change_percent
                trending_list.append(data)

        # Ordenar por performance
        trending_list.sort(
            key=lambda x: x.get('change_percent', 0), reverse=True
        )

        return trending_list


class AsyncCoinGeckoProvider(AsyncDataProvider):
    """Provedor assíncrono para CoinGecko com otimizações"""

    def __init__(self):
        super().__init__(
            max_concurrent=5, timeout=30
        )  # CoinGecko tem rate limits mais restritivos
        self.base_url = 'https://api.coingecko.com/api/v3'
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
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
        }

    async def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma criptomoeda específica"""
        async with self.semaphore:
            start_time = time.time()

            try:
                # Executar operação síncrona em thread separada
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None, self._fetch_crypto_sync, symbol
                )

                self.request_count += 1
                self.total_time += time.time() - start_time

                return data

            except Exception as e:
                self.error_count += 1
                print(f'⚠️ Erro ao buscar crypto {symbol}: {e}')
                return None

    def _fetch_crypto_sync(self, symbol: str) -> Optional[Dict]:
        """Busca dados de criptomoeda de forma síncrona"""
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
            print(f'Erro no _fetch_crypto_sync para {symbol}: {e}')
            return None

    async def get_multiple_cryptos(
        self, symbols: List[str]
    ) -> Dict[str, Dict]:
        """Busca múltiplas criptomoedas com controle de rate limit"""
        results = {}

        # Processar em batches menores para respeitar rate limits
        batch_size = 3

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]

            tasks = []
            for symbol in batch:
                task = asyncio.create_task(self.get_crypto_data(symbol))
                tasks.append((symbol, task))

            # Aguardar batch atual
            completed_tasks = await asyncio.gather(
                *[task for _, task in tasks], return_exceptions=True
            )

            for (symbol, _), result in zip(tasks, completed_tasks):
                if isinstance(result, Exception):
                    print(f'⚠️ Erro ao buscar crypto {symbol}: {result}')
                elif result:
                    results[symbol.upper()] = result

            # Aguardar entre batches para respeitar rate limits
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.5)

        return results

    async def get_trending_cryptos(self, limit: int = 10) -> List[Dict]:
        """Busca criptomoedas em alta usando batch otimizado"""
        symbols = Config.DEFAULT_CRYPTOS[:limit]
        cryptos_data = await self.get_multiple_cryptos(symbols)

        # Converter para lista e ordenar
        trending_list = list(cryptos_data.values())
        trending_list.sort(
            key=lambda x: x.get('change_percent_24h', 0), reverse=True
        )

        return trending_list[:limit]

    async def get_trending_from_api(self, limit: int = 10) -> List[Dict]:
        """Busca trending diretamente da API do CoinGecko (método alternativo)"""
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                coins = await loop.run_in_executor(
                    None,
                    lambda: self.cg.get_coins_markets(
                        vs_currency='usd',
                        order='percent_change_24h_desc',
                        per_page=limit,
                        page=1,
                        sparkline=False,
                        price_change_percentage='24h',
                    ),
                )

                result = []
                for coin in coins:
                    current_price = coin.get('current_price', 0)
                    price_change_24h = coin.get(
                        'price_change_percentage_24h', 0
                    )

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
                print(f'⚠️ Erro ao buscar trending do CoinGecko: {e}')
                return []


# ================================
# MOCK PROVIDERS ASSÍNCRONOS
# ================================


class AsyncMockStockProvider(AsyncDataProvider):
    """Provedor mock assíncrono para desenvolvimento"""

    def __init__(self):
        super().__init__()
        self.mock_data = self._generate_mock_data()

    def _generate_mock_data(self):
        """Gera dados mock para ações"""
        import random

        base_time = datetime.now()

        return {
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
            # Adicionar mais dados mock conforme necessário
        }

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Retorna dados mock de uma ação"""
        await asyncio.sleep(0.1)  # Simular latência
        return self.mock_data.get(symbol.upper())

    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Retorna dados mock de múltiplas ações"""
        await asyncio.sleep(0.2)  # Simular latência
        result = {}
        for symbol in symbols:
            data = self.mock_data.get(symbol.upper())
            if data:
                result[symbol.upper()] = data
        return result


class AsyncMockCryptoProvider(AsyncDataProvider):
    """Provedor mock assíncrono para criptomoedas"""

    def __init__(self):
        super().__init__()
        self.mock_data = self._generate_mock_data()

    def _generate_mock_data(self):
        """Gera dados mock para criptomoedas"""
        import random

        base_time = datetime.now()

        return {
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
            # Adicionar mais dados mock conforme necessário
        }

    async def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Retorna dados mock de uma criptomoeda"""
        await asyncio.sleep(0.1)  # Simular latência
        return self.mock_data.get(symbol.upper())

    async def get_multiple_cryptos(
        self, symbols: List[str]
    ) -> Dict[str, Dict]:
        """Retorna dados mock de múltiplas criptomoedas"""
        await asyncio.sleep(0.2)  # Simular latência
        result = {}
        for symbol in symbols:
            data = self.mock_data.get(symbol.upper())
            if data:
                result[symbol.upper()] = data
        return result
