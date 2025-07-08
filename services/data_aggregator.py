"""
Data Aggregator
Agregador inteligente que combina cache e provedores de dados para máxima performance
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.async_data_providers import (AsyncCoinGeckoProvider,
                                           AsyncMockCryptoProvider,
                                           AsyncMockStockProvider,
                                           AsyncYahooProvider)
from services.cache_manager import FinancialDataCache
from utils.config import Config


class DataAggregator:
    """Agregador principal que gerencia cache e provedores de dados"""

    def __init__(self):
        self.cache = FinancialDataCache()

        # Provedores de dados
        if Config.USE_MOCK_DATA:
            self.stock_provider = AsyncMockStockProvider()
            self.crypto_provider = AsyncMockCryptoProvider()
        else:
            self.stock_provider = AsyncYahooProvider()
            self.crypto_provider = AsyncCoinGeckoProvider()

        # Estatísticas
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'errors': 0,
        }

    async def initialize(self):
        """Inicializa o agregador e seus componentes"""
        print('🔧 Inicializando Data Aggregator...')

        await self.cache.initialize()
        await self.stock_provider.initialize()
        await self.crypto_provider.initialize()

        print('✅ Data Aggregator inicializado')

    async def close(self):
        """Finaliza o agregador"""
        await self.cache.close()
        await self.stock_provider.close()
        await self.crypto_provider.close()

    # ================================
    # MÉTODOS PARA AÇÕES
    # ================================

    async def get_stock_data(
        self, symbol: str, force_refresh: bool = False
    ) -> Optional[Dict]:
        """Busca dados de uma ação com cache inteligente"""
        symbol = symbol.upper()

        # Tentar cache primeiro (se não for refresh forçado)
        if not force_refresh:
            cached_data = await self.cache.get_stock_data(symbol)
            if cached_data:
                self.stats['cache_hits'] += 1
                return cached_data

        # Cache miss - buscar da API
        self.stats['cache_misses'] += 1
        self.stats['api_calls'] += 1

        try:
            data = await self.stock_provider.get_stock_data(symbol)

            if data:
                # Adicionar ao cache
                await self.cache.cache_stock_data(symbol, data)
                return data
            else:
                self.stats['errors'] += 1
                return None

        except Exception as e:
            self.stats['errors'] += 1
            print(f'⚠️ Erro ao buscar dados da ação {symbol}: {e}')
            return None

    async def batch_get_stocks(
        self, symbols: List[str], force_refresh: bool = False
    ) -> List[Dict]:
        """Busca múltiplas ações otimizando cache e API calls"""
        symbols = [s.upper() for s in symbols]
        results = []
        symbols_to_fetch = []

        # Primeiro, verificar o que está no cache
        if not force_refresh:
            cached_data = await self.cache.get_batch(symbols, 'stocks')

            for symbol in symbols:
                if symbol in cached_data:
                    results.append(cached_data[symbol])
                    self.stats['cache_hits'] += 1
                else:
                    symbols_to_fetch.append(symbol)
                    self.stats['cache_misses'] += 1
        else:
            symbols_to_fetch = symbols
            self.stats['cache_misses'] += len(symbols)

        # Buscar dados que não estão no cache
        if symbols_to_fetch:
            self.stats['api_calls'] += len(symbols_to_fetch)

            try:
                fresh_data = await self.stock_provider.get_multiple_stocks(
                    symbols_to_fetch
                )

                # Adicionar ao cache e resultados
                cache_batch = {}
                for symbol, data in fresh_data.items():
                    if data:
                        cache_batch[symbol] = data
                        results.append(data)

                # Cache em lote
                if cache_batch:
                    await self.cache.set_batch(cache_batch, 'stocks')

            except Exception as e:
                self.stats['errors'] += len(symbols_to_fetch)
                print(f'⚠️ Erro ao buscar lote de ações: {e}')

        return results

    async def get_trending_stocks(
        self, region: str = 'all', limit: int = 10, force_refresh: bool = False
    ) -> List[Dict]:
        """Busca ações em alta com cache específico para trending"""
        cache_key = f'stocks_{region}_{limit}'

        # Verificar cache de trending
        if not force_refresh:
            cached_trending = await self.cache.get_trending_data(
                'stocks', f'{region}_{limit}'
            )
            if cached_trending:
                self.stats['cache_hits'] += 1
                return cached_trending

        self.stats['cache_misses'] += 1

        # Determinar símbolos baseado na região
        if region == 'BR':
            symbols = Config.BRAZILIAN_STOCKS[
                : limit * 2
            ]  # Buscar mais para filtrar os melhores
        elif region == 'US':
            symbols = Config.US_STOCKS[: limit * 2]
        else:
            symbols = Config.DEFAULT_STOCKS[: limit * 2]

        # Buscar dados
        stocks_data = await self.batch_get_stocks(symbols, force_refresh)

        # Ordenar por performance e limitar
        trending_stocks = sorted(
            stocks_data, key=lambda x: x.get('change_percent', 0), reverse=True
        )[:limit]

        # Cache o resultado
        await self.cache.cache_trending_data(
            'stocks', f'{region}_{limit}', trending_stocks
        )

        return trending_stocks

    # ================================
    # MÉTODOS PARA CRIPTOMOEDAS
    # ================================

    async def get_crypto_data(
        self, symbol: str, force_refresh: bool = False
    ) -> Optional[Dict]:
        """Busca dados de uma criptomoeda com cache inteligente"""
        symbol = symbol.upper()

        # Tentar cache primeiro
        if not force_refresh:
            cached_data = await self.cache.get_crypto_data(symbol)
            if cached_data:
                self.stats['cache_hits'] += 1
                return cached_data

        # Cache miss - buscar da API
        self.stats['cache_misses'] += 1
        self.stats['api_calls'] += 1

        try:
            data = await self.crypto_provider.get_crypto_data(symbol)

            if data:
                # Adicionar ao cache
                await self.cache.cache_crypto_data(symbol, data)
                return data
            else:
                self.stats['errors'] += 1
                return None

        except Exception as e:
            self.stats['errors'] += 1
            print(f'⚠️ Erro ao buscar dados da criptomoeda {symbol}: {e}')
            return None

    async def batch_get_cryptos(
        self, symbols: List[str], force_refresh: bool = False
    ) -> List[Dict]:
        """Busca múltiplas criptomoedas otimizando cache e API calls"""
        symbols = [s.upper() for s in symbols]
        results = []
        symbols_to_fetch = []

        # Verificar cache
        if not force_refresh:
            cached_data = await self.cache.get_batch(symbols, 'cryptos')

            for symbol in symbols:
                if symbol in cached_data:
                    results.append(cached_data[symbol])
                    self.stats['cache_hits'] += 1
                else:
                    symbols_to_fetch.append(symbol)
                    self.stats['cache_misses'] += 1
        else:
            symbols_to_fetch = symbols
            self.stats['cache_misses'] += len(symbols)

        # Buscar dados que não estão no cache
        if symbols_to_fetch:
            self.stats['api_calls'] += len(symbols_to_fetch)

            try:
                fresh_data = await self.crypto_provider.get_multiple_cryptos(
                    symbols_to_fetch
                )

                # Adicionar ao cache e resultados
                cache_batch = {}
                for symbol, data in fresh_data.items():
                    if data:
                        cache_batch[symbol] = data
                        results.append(data)

                # Cache em lote
                if cache_batch:
                    await self.cache.set_batch(cache_batch, 'cryptos')

            except Exception as e:
                self.stats['errors'] += len(symbols_to_fetch)
                print(f'⚠️ Erro ao buscar lote de criptomoedas: {e}')

        return results

    async def get_trending_cryptos(
        self, limit: int = 10, force_refresh: bool = False
    ) -> List[Dict]:
        """Busca criptomoedas em alta"""
        cache_key = f'cryptos_trending_{limit}'

        # Verificar cache
        if not force_refresh:
            cached_trending = await self.cache.get_trending_data(
                'cryptos', str(limit)
            )
            if cached_trending:
                self.stats['cache_hits'] += 1
                return cached_trending

        self.stats['cache_misses'] += 1

        # Buscar dados
        symbols = Config.DEFAULT_CRYPTOS[
            : limit * 2
        ]  # Buscar mais para filtrar
        cryptos_data = await self.batch_get_cryptos(symbols, force_refresh)

        # Ordenar por performance 24h
        trending_cryptos = sorted(
            cryptos_data,
            key=lambda x: x.get('change_percent_24h', 0),
            reverse=True,
        )[:limit]

        # Cache o resultado
        await self.cache.cache_trending_data(
            'cryptos', str(limit), trending_cryptos
        )

        return trending_cryptos

    # ================================
    # MÉTODOS DE BUSCA E UTILIDADES
    # ================================

    async def search_symbol(
        self, query: str, symbol_type: str = 'all'
    ) -> List[Dict]:
        """Busca por símbolo específico"""
        query = query.upper().strip()
        results = []

        if symbol_type in ['all', 'stocks']:
            # Tentar buscar como ação
            stock_data = await self.get_stock_data(query)
            if stock_data:
                stock_data['type'] = 'stock'
                results.append(stock_data)

        if symbol_type in ['all', 'cryptos']:
            # Tentar buscar como criptomoeda
            crypto_data = await self.get_crypto_data(query)
            if crypto_data:
                crypto_data['type'] = 'crypto'
                results.append(crypto_data)

        return results

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os componentes"""
        try:
            stock_health = await self.stock_provider.health_check()
            crypto_health = await self.crypto_provider.health_check()
            cache_health = await self.cache.health_check()

            return {
                'stock_provider': stock_health,
                'crypto_provider': crypto_health,
                'cache': cache_health,
                'aggregator_stats': self.stats,
            }
        except Exception as e:
            return {'error': str(e)}

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas"""
        cache_stats = await self.cache.get_stats()
        stock_stats = await self.stock_provider.health_check()
        crypto_stats = await self.crypto_provider.health_check()

        return {
            'aggregator': self.stats,
            'cache': cache_stats,
            'stock_provider': stock_stats,
            'crypto_provider': crypto_stats,
            'cache_hit_rate': (
                self.stats['cache_hits']
                / max(1, self.stats['cache_hits'] + self.stats['cache_misses'])
            )
            * 100,
        }

    # ================================
    # MÉTODOS DE MANUTENÇÃO
    # ================================

    async def warm_up_cache(self):
        """Aquece o cache com dados populares"""
        print('🔥 Aquecendo cache com dados populares...')

        try:
            # Carregar ações populares
            popular_stocks = Config.DEFAULT_STOCKS[:15]
            await self.batch_get_stocks(popular_stocks, force_refresh=True)

            # Carregar criptos populares
            popular_cryptos = Config.DEFAULT_CRYPTOS[:10]
            await self.batch_get_cryptos(popular_cryptos, force_refresh=True)

            # Carregar trending
            await self.get_trending_stocks(region='all', force_refresh=True)
            await self.get_trending_stocks(region='US', force_refresh=True)
            await self.get_trending_stocks(region='BR', force_refresh=True)
            await self.get_trending_cryptos(force_refresh=True)

            print('✅ Cache aquecido com sucesso')

        except Exception as e:
            print(f'⚠️ Erro ao aquecer cache: {e}')

    async def clear_cache(self, category: Optional[str] = None):
        """Limpa cache por categoria ou totalmente"""
        if category:
            count = await self.cache.clear_category(category)
            print(f'🧹 {count} itens removidos da categoria {category}')
        else:
            await self.cache.close()
            await self.cache.initialize()
            print('🧹 Cache completamente limpo')

    async def refresh_trending_data(self):
        """Atualiza dados de trending em background"""
        try:
            print('🔄 Atualizando dados de trending...')

            # Atualizar trending com refresh forçado
            await asyncio.gather(
                self.get_trending_stocks(region='all', force_refresh=True),
                self.get_trending_stocks(region='US', force_refresh=True),
                self.get_trending_stocks(region='BR', force_refresh=True),
                self.get_trending_cryptos(force_refresh=True),
                return_exceptions=True,
            )

            print('✅ Dados de trending atualizados')

        except Exception as e:
            print(f'⚠️ Erro ao atualizar trending: {e}')
