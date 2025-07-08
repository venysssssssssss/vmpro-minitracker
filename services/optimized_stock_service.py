"""
Serviço otimizado para dados de ações usando APIs assíncronas
Implementa IStockService seguindo princípios SOLID
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import time

import aiohttp
import pandas as pd
import ujson
import yfinance as yf

from interfaces.service_interfaces import IStockService, DataSourceStatus
from .fallback_data_service import FallbackDataService


class OptimizedStockService(IStockService):
    """Serviço otimizado para busca de dados de ações com performance melhorada"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)  # Reduzir workers para evitar rate limit
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Aumentar TTL para 15 minutos
        self.request_semaphore = asyncio.Semaphore(2)  # Máximo 2 requests simultâneos
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Mínimo 1 segundo entre requests para o mesmo símbolo
        self._status = DataSourceStatus.AVAILABLE
        self._consecutive_failures = 0
        self._max_failures = 5

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma ação específica de forma otimizada"""
        cache_key = f'stock_{symbol}'

        # Verificar cache primeiro
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data

        # Rate limiting por símbolo
        current_time = time.time()
        if symbol in self.last_request_time:
            time_since_last = current_time - self.last_request_time[symbol]
            if time_since_last < self.min_request_interval:
                # Se muito recente, retornar dados em cache (mesmo que expirados) ou None
                if cache_key in self.cache:
                    cached_data, _ = self.cache[cache_key]
                    return cached_data
                return None

        try:
            # Usar semáforo para limitar requests simultâneos
            async with self.request_semaphore:
                self.last_request_time[symbol] = current_time
                
                # Adicionar delay adicional para evitar rate limiting
                await asyncio.sleep(0.5)
                
                # Usar ThreadPoolExecutor para não bloquear o event loop
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    self.executor, self._fetch_single_stock, symbol
                )

                if data:
                    self.cache[cache_key] = (data, datetime.now())
                    self._update_status(True)
                else:
                    self._update_status(False)

                return data

        except Exception as e:
            print(f'Erro ao buscar dados para {symbol}: {e}')
            self._update_status(False)
            # Em caso de erro, tentar retornar dados em cache
            if cache_key in self.cache:
                cached_data, _ = self.cache[cache_key]
                return cached_data
            return None

    def _fetch_single_stock(self, symbol: str) -> Optional[Dict]:
        """Função síncrona para buscar dados de uma ação"""
        try:
            ticker = yf.Ticker(symbol)

            # Buscar informações básicas com timeout
            try:
                info = ticker.info
            except Exception as e:
                print(f'Erro ao buscar info para {symbol}: {e}')
                info = {}

            # Buscar histórico com tratamento de erro
            try:
                hist = ticker.history(period='5d', interval='1d')
            except Exception as e:
                print(f'Erro ao buscar histórico para {symbol}: {e}')
                return None

            if hist.empty:
                return None

            current_price = float(hist['Close'].iloc[-1])
            previous_close = (
                float(hist['Close'].iloc[-2])
                if len(hist) > 1
                else current_price
            )
            current_volume = (
                int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
            )

            # Calcular indicadores técnicos simples
            prices = hist['Close'].values
            sma_5 = float(
                pd.Series(prices)
                .rolling(window=min(5, len(prices)))
                .mean()
                .iloc[-1]
            )

            # Calcular volatilidade (desvio padrão dos últimos 5 dias)
            volatility = (
                float(pd.Series(prices).pct_change().std() * 100)
                if len(prices) > 1
                else 0
            )

            # Calcular mudança percentual
            change_percent = (
                ((current_price - previous_close) / previous_close * 100)
                if previous_close > 0
                else 0
            )
            change_amount = current_price - previous_close

            return {
                'symbol': symbol.upper(),
                'name': info.get(
                    'longName', info.get('shortName', symbol.upper())
                ),
                'price': round(current_price, 2),
                'previous_close': round(previous_close, 2),
                'change_amount': round(change_amount, 2),
                'change_percent': round(change_percent, 2),
                'market_cap': info.get('marketCap'),
                'volume': current_volume,
                'sma_5': round(sma_5, 2),
                'volatility': round(volatility, 2),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'last_updated': datetime.now().isoformat(),
            }

        except Exception as e:
            print(f'Erro ao buscar {symbol}: {e}')
            return None

    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca dados de múltiplas ações em paralelo com rate limiting"""
        # Dividir em lotes menores para evitar rate limiting
        batch_size = 3
        results = {}
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            tasks = [self.get_stock_data(symbol) for symbol in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, dict) and result:
                    results[symbol.upper()] = result
            
            # Delay entre lotes para evitar rate limiting
            if i + batch_size < len(symbols):
                await asyncio.sleep(2.0)

        return results

    async def get_trending_stocks(
        self, limit: int = 10, region: str = 'US'
    ) -> List[Dict]:
        """Busca ações em alta com base na região"""
        try:
            if region.upper() == 'BR':
                symbols = [
                    'VALE3.SA',
                    'PETR4.SA',
                    'ITUB4.SA',
                    'BBDC4.SA',
                    'ABEV3.SA',
                    'WEGE3.SA',
                    'RENT3.SA',
                    'MGLU3.SA',
                    'B3SA3.SA',
                    'SUZB3.SA',
                    'JBSS3.SA',
                    'LREN3.SA',
                    'TOTS3.SA',
                    'RADL3.SA',
                    'VIVT3.SA',
                ]
            else:  # US
                symbols = [
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
                    'UNH',
                    'HD',
                    'PG',
                    'JNJ',
                    'MA',
                ]

            # Buscar dados de todas as ações em paralelo
            stocks_data = await self.get_multiple_stocks(
                symbols[: min(limit * 2, len(symbols))]
            )

            # Filtrar apenas ações com dados válidos e ordenar por performance
            valid_stocks = []
            for symbol, data in stocks_data.items():
                if data and data.get('change_percent') is not None:
                    valid_stocks.append(data)

            # Se não temos dados suficientes, usar dados de fallback
            if len(valid_stocks) < limit // 2:
                print(f"Poucos dados reais disponíveis ({len(valid_stocks)}), usando dados de fallback")
                fallback_stocks = FallbackDataService.get_sample_trending_stocks(region, limit)
                return fallback_stocks

            # Ordenar por mudança percentual (descendente)
            valid_stocks.sort(
                key=lambda x: x.get('change_percent', 0), reverse=True
            )

            return valid_stocks[:limit]

        except Exception as e:
            print(f'Erro ao buscar ações em alta: {e}')
            # Em caso de erro, retornar dados de fallback
            return FallbackDataService.get_sample_trending_stocks(region, limit)

    async def get_market_overview(self, region: str = 'US') -> Dict:
        """Retorna uma visão geral do mercado"""
        try:
            # Índices principais por região
            if region.upper() == 'BR':
                indices = ['^BVSP']  # Ibovespa
                main_stocks = ['VALE3.SA', 'PETR4.SA', 'ITUB4.SA', 'BBDC4.SA']
            else:
                indices = [
                    '^GSPC',
                    '^DJI',
                    '^IXIC',
                ]  # S&P 500, Dow Jones, NASDAQ
                main_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

            # Buscar dados dos índices e principais ações
            all_symbols = indices + main_stocks
            data = await self.get_multiple_stocks(all_symbols)

            # Separar índices e ações
            indices_data = {
                k: v
                for k, v in data.items()
                if k in [s.replace('^', '') for s in indices]
            }
            stocks_data = {k: v for k, v in data.items() if k in main_stocks}

            # Calcular estatísticas do mercado
            total_volume = sum(
                stock.get('volume', 0) for stock in stocks_data.values()
            )
            avg_change = (
                sum(
                    stock.get('change_percent', 0)
                    for stock in stocks_data.values()
                )
                / len(stocks_data)
                if stocks_data
                else 0
            )

            return {
                'region': region.upper(),
                'indices': indices_data,
                'top_stocks': stocks_data,
                'market_stats': {
                    'total_volume': total_volume,
                    'average_change': round(avg_change, 2),
                    'timestamp': datetime.now().isoformat(),
                },
            }

        except Exception as e:
            print(f'Erro ao buscar visão geral do mercado: {e}')
            return {}

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

    # Implementação da interface IDataService
    async def get_data(self, identifier: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Implementação genérica - delega para get_stock_data"""
        return await self.get_stock_data(identifier)
    
    async def get_multiple_data(self, identifiers: List[str], **kwargs) -> Dict[str, Dict[str, Any]]:
        """Implementação genérica - delega para get_multiple_stocks"""
        return await self.get_multiple_stocks(identifiers)
    
    async def get_trending_data(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Implementação genérica - delega para get_trending_stocks"""
        region = kwargs.get("region", "US")
        return await self.get_trending_stocks(region, limit)
    
    def get_service_status(self) -> DataSourceStatus:
        """Retorna status atual do serviço"""
        return self._status
    
    def _update_status(self, success: bool) -> None:
        """Atualiza status baseado no sucesso da operação"""
        if success:
            self._consecutive_failures = 0
            if self._status == DataSourceStatus.RATE_LIMITED:
                self._status = DataSourceStatus.AVAILABLE
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._status = DataSourceStatus.ERROR
            elif "429" in str(self._consecutive_failures):  # Rate limit detection
                self._status = DataSourceStatus.RATE_LIMITED
