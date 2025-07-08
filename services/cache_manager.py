"""
Cache Manager Assíncrono
Sistema de cache otimizado para alta performance
"""

import asyncio
import time
import weakref
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import ujson as json


class CacheManager:
    """Gerenciador de cache em memória com TTL e estratégias inteligentes"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = asyncio.Lock()

        # Estatísticas por tipo de dados
        self.stats = defaultdict(lambda: {'hits': 0, 'misses': 0, 'size': 0})

    async def initialize(self):
        """Inicializa o cache manager"""
        print('🔧 Inicializando Cache Manager...')

        # Iniciar limpeza periódica
        asyncio.create_task(self._periodic_cleanup())

    async def get(self, key: str, category: str = 'default') -> Optional[Any]:
        """Busca item no cache"""
        async with self.lock:
            full_key = f'{category}:{key}'

            if full_key in self.cache:
                cache_item = self.cache[full_key]

                # Verificar TTL
                if time.time() - cache_item['timestamp'] < cache_item['ttl']:
                    self.access_times[full_key] = time.time()
                    self.hit_count += 1
                    self.stats[category]['hits'] += 1
                    return cache_item['data']
                else:
                    # Item expirado
                    await self._remove_item(full_key, category)

            self.miss_count += 1
            self.stats[category]['misses'] += 1
            return None

    async def set(
        self,
        key: str,
        data: Any,
        category: str = 'default',
        ttl: Optional[int] = None,
    ) -> None:
        """Armazena item no cache"""
        async with self.lock:
            full_key = f'{category}:{key}'
            ttl = ttl or self.default_ttl

            # Remover item existente se houver
            if full_key in self.cache:
                await self._remove_item(full_key, category)

            # Verificar se precisa fazer cleanup por tamanho
            if len(self.cache) >= self.max_size:
                await self._evict_least_recently_used()

            # Adicionar novo item
            self.cache[full_key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl,
                'category': category,
            }
            self.access_times[full_key] = time.time()
            self.stats[category]['size'] += 1

    async def delete(self, key: str, category: str = 'default') -> bool:
        """Remove item do cache"""
        async with self.lock:
            full_key = f'{category}:{key}'
            if full_key in self.cache:
                await self._remove_item(full_key, category)
                return True
            return False

    async def clear_category(self, category: str) -> int:
        """Limpa todos os itens de uma categoria"""
        async with self.lock:
            keys_to_remove = [
                k for k in self.cache.keys() if k.startswith(f'{category}:')
            ]
            count = 0

            for key in keys_to_remove:
                await self._remove_item(key, category)
                count += 1

            return count

    async def get_batch(
        self, keys: List[str], category: str = 'default'
    ) -> Dict[str, Any]:
        """Busca múltiplos itens do cache"""
        results = {}

        for key in keys:
            value = await self.get(key, category)
            if value is not None:
                results[key] = value

        return results

    async def set_batch(
        self,
        items: Dict[str, Any],
        category: str = 'default',
        ttl: Optional[int] = None,
    ) -> None:
        """Armazena múltiplos itens no cache"""
        for key, data in items.items():
            await self.set(key, data, category, ttl)

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cache"""
        return {
            'status': 'healthy',
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': self._calculate_hit_rate(),
            'categories': dict(self.stats),
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache"""
        return {
            'total_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self._calculate_hit_rate(),
            'categories': dict(self.stats),
            'memory_usage': self._estimate_memory_usage(),
        }

    async def _remove_item(self, full_key: str, category: str) -> None:
        """Remove item do cache (método interno)"""
        if full_key in self.cache:
            del self.cache[full_key]
        if full_key in self.access_times:
            del self.access_times[full_key]
        self.stats[category]['size'] -= 1

    async def _evict_least_recently_used(self) -> None:
        """Remove item menos recentemente usado"""
        if not self.access_times:
            return

        # Encontrar item menos usado
        oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]

        # Determinar categoria
        category = (
            self.cache[oldest_key]['category']
            if oldest_key in self.cache
            else 'unknown'
        )

        await self._remove_item(oldest_key, category)

    async def _periodic_cleanup(self) -> None:
        """Limpeza periódica de itens expirados"""
        while True:
            try:
                await asyncio.sleep(60)  # Executar a cada minuto

                expired_keys = []
                current_time = time.time()

                async with self.lock:
                    for full_key, cache_item in self.cache.items():
                        if (
                            current_time - cache_item['timestamp']
                            > cache_item['ttl']
                        ):
                            expired_keys.append(
                                (full_key, cache_item['category'])
                            )

                # Remover itens expirados
                for full_key, category in expired_keys:
                    async with self.lock:
                        await self._remove_item(full_key, category)

                if expired_keys:
                    print(
                        f'🧹 Cache: {len(expired_keys)} itens expirados removidos'
                    )

            except Exception as e:
                print(f'⚠️ Erro na limpeza do cache: {e}')

    def _calculate_hit_rate(self) -> float:
        """Calcula taxa de hit do cache"""
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return (self.hit_count / total_requests) * 100

    def _estimate_memory_usage(self) -> Dict[str, Any]:
        """Estima uso de memória do cache"""
        try:
            import sys

            total_size = 0
            for key, item in self.cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(item)
                if isinstance(item['data'], (dict, list)):
                    total_size += sys.getsizeof(str(item['data']))

            return {
                'estimated_bytes': total_size,
                'estimated_mb': round(total_size / (1024 * 1024), 2),
                'items_count': len(self.cache),
            }
        except Exception:
            return {'error': 'Could not estimate memory usage'}

    async def close(self) -> None:
        """Limpa o cache ao fechar"""
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.stats.clear()
        print('🔧 Cache Manager finalizado')


# ================================
# CACHE ESPECIALIZADO PARA DADOS FINANCEIROS
# ================================


class FinancialDataCache(CacheManager):
    """Cache especializado para dados financeiros com estratégias específicas"""

    def __init__(self):
        super().__init__(max_size=2000, default_ttl=300)

        # TTLs específicos por tipo de dados
        self.ttl_config = {
            'stocks': 240,  # 4 minutos para ações
            'cryptos': 180,  # 3 minutos para criptos (mais voláteis)
            'market_status': 600,  # 10 minutos para status do mercado
            'trending': 120,  # 2 minutos para trending
            'search': 900,  # 15 minutos para resultados de busca
        }

    async def cache_stock_data(self, symbol: str, data: Dict) -> None:
        """Cache específico para dados de ações"""
        await self.set(
            key=symbol.upper(),
            data=data,
            category='stocks',
            ttl=self.ttl_config['stocks'],
        )

    async def cache_crypto_data(self, symbol: str, data: Dict) -> None:
        """Cache específico para dados de criptomoedas"""
        await self.set(
            key=symbol.upper(),
            data=data,
            category='cryptos',
            ttl=self.ttl_config['cryptos'],
        )

    async def cache_trending_data(
        self, data_type: str, region: str, data: List
    ) -> None:
        """Cache para dados de trending"""
        key = f'{data_type}_{region}'
        await self.set(
            key=key,
            data=data,
            category='trending',
            ttl=self.ttl_config['trending'],
        )

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de ação no cache"""
        return await self.get(symbol.upper(), 'stocks')

    async def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de criptomoeda no cache"""
        return await self.get(symbol.upper(), 'cryptos')

    async def get_trending_data(
        self, data_type: str, region: str
    ) -> Optional[List]:
        """Busca dados de trending no cache"""
        key = f'{data_type}_{region}'
        return await self.get(key, 'trending')

    async def preload_popular_symbols(
        self, stocks: List[str], cryptos: List[str]
    ) -> None:
        """Pre-carrega símbolos populares no cache"""
        print(
            f'📊 Pre-carregando {len(stocks)} ações e {len(cryptos)} criptos no cache...'
        )

        # Implementação específica seria feita com os provedores de dados
        # Por agora, apenas registramos a intenção
        for symbol in stocks:
            await self.set(f'preload_{symbol}', True, 'metadata', 3600)

        for symbol in cryptos:
            await self.set(f'preload_{symbol}', True, 'metadata', 3600)

    async def clear_all(self) -> None:
        """Limpa todos os dados do cache"""
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()
            
            # Reset das estatísticas
            self.hit_count = 0
            self.miss_count = 0
            
            # Reset das estatísticas por categoria
            for category in self.stats:
                self.stats[category] = {'hits': 0, 'misses': 0, 'size': 0}


# Instância global do cache
cache_manager = FinancialDataCache()
