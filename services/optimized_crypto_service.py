"""
Serviço otimizado para dados de criptomoedas usando APIs assíncronas
Implementa ICryptoService seguindo princípios SOLID
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pycoingecko import CoinGeckoAPI
from interfaces.service_interfaces import ICryptoService, DataSourceStatus
from .fallback_data_service import FallbackDataService


class OptimizedCryptoService(ICryptoService):
    """Serviço otimizado para busca de dados de criptomoedas com performance melhorada"""

    def __init__(self):
        self.cg = CoinGeckoAPI()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.cache = {}
        self.cache_ttl = timedelta(
            minutes=3
        )  # Cache menor para crypto (mais volátil)
        self._status = DataSourceStatus.AVAILABLE
        self._consecutive_failures = 0
        self._max_failures = 5

        # Mapping otimizado de símbolos para IDs do CoinGecko
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'SOL': 'solana',
            'TRX': 'tron',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LTC': 'litecoin',
            'SHIB': 'shiba-inu',
            'AVAX': 'avalanche-2',
            'UNI': 'uniswap',
            'LINK': 'chainlink',
            'ATOM': 'cosmos',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'BCH': 'bitcoin-cash',
            'FIL': 'filecoin',
        }

    # Implementação da interface IDataService
    async def get_data(self, identifier: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Implementação genérica - delega para get_crypto_data"""
        return await self.get_crypto_data(identifier)
    
    async def get_multiple_data(self, identifiers: List[str], **kwargs) -> Dict[str, Dict[str, Any]]:
        """Implementação genérica - busca múltiplas criptomoedas"""
        results = {}
        for identifier in identifiers:
            data = await self.get_crypto_data(identifier)
            if data:
                results[identifier.upper()] = data
        return results
    
    async def get_trending_data(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Implementação genérica - delega para get_trending_cryptos"""
        order_by = kwargs.get("order_by", "percent_change_24h")
        return await self.get_trending_cryptos(order_by, limit)
    
    def get_service_status(self) -> DataSourceStatus:
        """Retorna status atual do serviço"""
        return self._status
    
    def _update_status(self, success: bool) -> None:
        """Atualiza status baseado no sucesso da operação"""
        if success:
            self._consecutive_failures = 0
            if self._status in [DataSourceStatus.ERROR, DataSourceStatus.RATE_LIMITED]:
                self._status = DataSourceStatus.AVAILABLE
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._status = DataSourceStatus.ERROR

    async def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma criptomoeda específica de forma otimizada"""
        cache_key = f'crypto_{symbol.upper()}'

        # Verificar cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, self._fetch_single_crypto, symbol
            )

            if data:
                self.cache[cache_key] = (data, datetime.now())

            return data

        except Exception as e:
            print(f'Erro ao buscar dados para {symbol}: {e}')
            return None

    def _fetch_single_crypto(self, symbol: str) -> Optional[Dict]:
        """Função síncrona para buscar dados de uma criptomoeda"""
        try:
            crypto_id = self.symbol_to_id.get(symbol.upper())

            if not crypto_id:
                # Buscar ID usando search API
                search_results = self.cg.search(query=symbol)
                if search_results and search_results.get('coins'):
                    crypto_id = search_results['coins'][0]['id']
                    # Adicionar ao mapping para futuras consultas
                    self.symbol_to_id[symbol.upper()] = crypto_id
                else:
                    return None

            # Buscar dados detalhados
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
            price_change_7d = market_data.get('price_change_percentage_7d', 0)
            price_change_30d = market_data.get(
                'price_change_percentage_30d', 0
            )

            # Calcular preço anterior baseado na mudança de 24h
            if price_change_24h != 0:
                previous_price = current_price / (1 + (price_change_24h / 100))
            else:
                previous_price = current_price

            # Dados adicionais de mercado
            market_cap = market_data.get('market_cap', {}).get('usd')
            volume_24h = market_data.get('total_volume', {}).get('usd')
            circulating_supply = market_data.get('circulating_supply')
            total_supply = market_data.get('total_supply')
            max_supply = market_data.get('max_supply')

            # Rankings
            market_cap_rank = data.get('market_cap_rank')
            coingecko_rank = data.get('coingecko_rank')

            return {
                'symbol': symbol.upper(),
                'name': data.get('name', symbol),
                'price': round(current_price, 8)
                if current_price < 1
                else round(current_price, 2),
                'previous_close': round(previous_price, 8)
                if previous_price < 1
                else round(previous_price, 2),
                'change_amount': round(current_price - previous_price, 8)
                if current_price < 1
                else round(current_price - previous_price, 2),
                'change_percent_24h': round(price_change_24h, 2),
                'change_percent_7d': round(price_change_7d, 2),
                'change_percent_30d': round(price_change_30d, 2),
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'circulating_supply': circulating_supply,
                'total_supply': total_supply,
                'max_supply': max_supply,
                'market_cap_rank': market_cap_rank,
                'coingecko_rank': coingecko_rank,
                'image': data.get('image', {}).get('small', ''),
                'last_updated': datetime.now().isoformat(),
            }

        except Exception as e:
            print(f'Erro ao buscar {symbol}: {e}')
            return None

    async def get_multiple_cryptos(
        self, symbols: List[str]
    ) -> Dict[str, Dict]:
        """Busca dados de múltiplas criptomoedas em paralelo"""
        tasks = [self.get_crypto_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict) and result:
                data[symbol.upper()] = result

        return data

    async def get_trending_cryptos(
        self, limit: int = 10, order_by: str = 'percent_change_24h'
    ) -> List[Dict]:
        """Busca criptomoedas em alta usando a API otimizada do CoinGecko"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, self._fetch_trending_cryptos, limit, order_by
            )

            return data

        except Exception as e:
            print(f'Erro ao buscar criptos em alta: {e}')
            # Retornar dados de fallback em caso de erro
            return FallbackDataService.get_sample_trending_cryptos(limit, order_by)

    def _fetch_trending_cryptos(self, limit: int, order_by: str) -> List[Dict]:
        """Busca criptomoedas em alta (função síncrona)"""
        try:
            # Validar e converter parâmetros
            limit = int(limit) if isinstance(limit, str) else limit
            limit = max(1, min(limit, 250))  # CoinGecko limit
            
            # Mapear ordem para formato do CoinGecko
            order_mapping = {
                'percent_change_24h': 'percent_change_24h_desc',
                'market_cap': 'market_cap_desc',
                'volume': 'volume_desc',
                'price': 'price_desc',
            }

            order = order_mapping.get(order_by, 'percent_change_24h_desc')

            coins = self.cg.get_coins_markets(
                vs_currency='usd',
                order=order,
                per_page=limit,
                page=1,
                sparkline=False,
                price_change_percentage='24h,7d,30d',
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
                        'price': round(current_price, 8)
                        if current_price < 1
                        else round(current_price, 2),
                        'previous_close': round(previous_price, 8)
                        if previous_price < 1
                        else round(previous_price, 2),
                        'change_amount': round(
                            current_price - previous_price, 8
                        )
                        if current_price < 1
                        else round(current_price - previous_price, 2),
                        'change_percent_24h': round(price_change_24h, 2),
                        'change_percent_7d': round(
                            coin.get(
                                'price_change_percentage_7d_in_currency', 0
                            ),
                            2,
                        ),
                        'change_percent_30d': round(
                            coin.get(
                                'price_change_percentage_30d_in_currency', 0
                            ),
                            2,
                        ),
                        'market_cap': coin.get('market_cap'),
                        'volume_24h': coin.get('total_volume'),
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'image': coin.get('image', ''),
                        'last_updated': datetime.now().isoformat(),
                    }
                )

            return result

        except Exception as e:
            print(f'Erro na busca de criptos trending: {e}')
            # Retornar dados de fallback em caso de erro
            return FallbackDataService.get_sample_trending_cryptos(limit, order_by)

    async def get_crypto_market_overview(self) -> Dict:
        """Retorna visão geral do mercado de criptomoedas"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, self._fetch_market_overview
            )

            return data

        except Exception as e:
            print(f'Erro ao buscar visão geral do mercado crypto: {e}')
            return {}

    def _fetch_market_overview(self) -> Dict:
        """Busca dados gerais do mercado de crypto"""
        try:
            # Buscar dados globais
            global_data = self.cg.get_global()

            # Buscar top 10 cryptos
            top_cryptos = self.cg.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=10,
                page=1,
                sparkline=False,
                price_change_percentage='24h',
            )

            # Calcular dominância
            total_market_cap = (
                global_data.get('data', {})
                .get('total_market_cap', {})
                .get('usd', 0)
            )
            btc_dominance = (
                global_data.get('data', {})
                .get('market_cap_percentage', {})
                .get('btc', 0)
            )
            eth_dominance = (
                global_data.get('data', {})
                .get('market_cap_percentage', {})
                .get('eth', 0)
            )

            return {
                'total_market_cap': total_market_cap,
                'total_volume_24h': global_data.get('data', {})
                .get('total_volume', {})
                .get('usd', 0),
                'btc_dominance': round(btc_dominance, 2),
                'eth_dominance': round(eth_dominance, 2),
                'active_cryptocurrencies': global_data.get('data', {}).get(
                    'active_cryptocurrencies', 0
                ),
                'markets': global_data.get('data', {}).get('markets', 0),
                'top_cryptos': top_cryptos[:5],  # Top 5 apenas
                'last_updated': datetime.now().isoformat(),
            }

        except Exception as e:
            print(f'Erro ao buscar overview do mercado: {e}')
            return {}

    async def search_crypto(self, query: str, limit: int = 10) -> List[Dict]:
        """Busca criptomoedas por nome ou símbolo"""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor, self._search_crypto, query, limit
            )

            return results

        except Exception as e:
            print(f'Erro ao buscar criptomoeda: {e}')
            return []

    def _search_crypto(self, query: str, limit: int) -> List[Dict]:
        """Busca criptomoeda (função síncrona)"""
        try:
            search_results = self.cg.search(query=query)
            coins = search_results.get('coins', [])[:limit]

            result = []
            for coin in coins:
                result.append(
                    {
                        'id': coin.get('id'),
                        'name': coin.get('name'),
                        'symbol': coin.get('symbol', '').upper(),
                        'thumb': coin.get('thumb'),
                        'market_cap_rank': coin.get('market_cap_rank'),
                    }
                )

            return result

        except Exception as e:
            print(f'Erro na busca: {e}')
            return []

    def clear_cache(self) -> bool:
        """Limpa o cache de dados"""
        try:
            self.cache.clear()
            return True
        except Exception:
            return False

    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        now = datetime.now()
        active_entries = sum(
            1
            for _, timestamp in self.cache.values()
            if now - timestamp < self.cache_ttl
        )

        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60,
        }
