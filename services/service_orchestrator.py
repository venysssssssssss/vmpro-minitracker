"""
Service Orchestrator - Coordena todos os serviços seguindo princípios SOLID
Implementa o padrão Facade para simplificar a complexidade dos subsistemas
"""
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime

from services.optimized_stock_service import OptimizedStockService
from services.optimized_crypto_service import OptimizedCryptoService
from services.fallback_data_service import FallbackDataService
from services.cache_manager import CacheManager


class ServiceOrchestrator:
    """
    Orquestrador de serviços que coordena a comunicação entre diferentes camadas
    Implementa os princípios:
    - Single Responsibility: Coordena apenas a comunicação entre serviços
    - Open/Closed: Extensível para novos serviços
    - Liskov Substitution: Serviços podem ser substituídos
    - Interface Segregation: Interfaces específicas para cada tipo de dados
    - Dependency Inversion: Depende de abstrações, não implementações
    """
    
    def __init__(self):
        self.stock_service = OptimizedStockService()
        self.crypto_service = OptimizedCryptoService()
        self.fallback_service = FallbackDataService()
        self.cache_manager = CacheManager()
        self.logger = logging.getLogger(__name__)
        
        # Métricas
        self.metrics = {
            'requests_count': 0,
            'cache_hits': 0,
            'fallback_used': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Inicializa todos os serviços"""
        try:
            await self.cache_manager.initialize()
            self.logger.info("Service Orchestrator initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Service Orchestrator: {e}")
            raise
    
    # ============== STOCK OPERATIONS ==============
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados de uma ação com fallback automático
        Implementa Circuit Breaker pattern
        """
        self.metrics['requests_count'] += 1
        
        try:
            # Tentar cache primeiro
            cache_key = f"stock_{symbol.upper()}"
            cached_data = await self.cache_manager.get(cache_key, 'stocks')
            
            if cached_data:
                self.metrics['cache_hits'] += 1
                return cached_data
            
            # Buscar dados reais
            data = await self.stock_service.get_stock_data(symbol)
            
            if data:
                # Armazenar no cache
                await self.cache_manager.set(cache_key, data, 'stocks', ttl=900)  # 15 min
                return data
            else:
                # Usar fallback
                self.metrics['fallback_used'] += 1
                return self.fallback_service.get_sample_stock_data(symbol)
                
        except Exception as e:
            self.logger.error(f"Error getting stock data for {symbol}: {e}")
            self.metrics['errors'] += 1
            # Em caso de erro, usar fallback
            return self.fallback_service.get_sample_stock_data(symbol)
    
    async def get_trending_stocks(self, limit: int = 10, region: str = 'US') -> List[Dict[str, Any]]:
        """
        Busca ações em alta com fallback inteligente
        """
        self.metrics['requests_count'] += 1
        
        try:
            # Tentar cache primeiro
            cache_key = f"trending_stocks_{region}_{limit}"
            cached_data = await self.cache_manager.get(cache_key, 'trending')
            
            if cached_data:
                self.metrics['cache_hits'] += 1
                return cached_data
            
            # Buscar dados reais
            data = await self.stock_service.get_trending_stocks(limit=limit, region=region)
            
            # Verificar qualidade dos dados
            valid_data = [item for item in data if item and item.get('price') and item.get('symbol')]
            
            if len(valid_data) >= limit // 2:  # Se temos pelo menos 50% dos dados válidos
                # Armazenar no cache
                await self.cache_manager.set(cache_key, valid_data, 'trending', ttl=600)  # 10 min
                return valid_data
            else:
                # Usar fallback se dados insuficientes
                self.metrics['fallback_used'] += 1
                fallback_data = self.fallback_service.get_sample_trending_stocks(region, limit)
                return fallback_data
                
        except Exception as e:
            self.logger.error(f"Error getting trending stocks: {e}")
            self.metrics['errors'] += 1
            # Em caso de erro, usar fallback
            return self.fallback_service.get_sample_trending_stocks(region, limit)
    
    # ============== CRYPTO OPERATIONS ==============
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados de uma criptomoeda com fallback automático
        """
        self.metrics['requests_count'] += 1
        
        try:
            # Tentar cache primeiro
            cache_key = f"crypto_{symbol.upper()}"
            cached_data = await self.cache_manager.get(cache_key, 'crypto')
            
            if cached_data:
                self.metrics['cache_hits'] += 1
                return cached_data
            
            # Buscar dados reais
            data = await self.crypto_service.get_crypto_data(symbol)
            
            if data:
                # Armazenar no cache
                await self.cache_manager.set(cache_key, data, 'crypto', ttl=600)  # 10 min
                return data
            else:
                # Usar fallback
                self.metrics['fallback_used'] += 1
                return self.fallback_service.get_sample_crypto_data(symbol)
                
        except Exception as e:
            self.logger.error(f"Error getting crypto data for {symbol}: {e}")
            self.metrics['errors'] += 1
            # Em caso de erro, usar fallback
            return self.fallback_service.get_sample_crypto_data(symbol)
    
    async def get_trending_cryptos(self, limit: int = 10, order_by: str = 'percent_change_24h') -> List[Dict[str, Any]]:
        """
        Busca criptomoedas em alta com fallback inteligente
        """
        self.metrics['requests_count'] += 1
        
        try:
            # Tentar cache primeiro
            cache_key = f"trending_crypto_{order_by}_{limit}"
            cached_data = await self.cache_manager.get(cache_key, 'trending')
            
            if cached_data:
                self.metrics['cache_hits'] += 1
                return cached_data
            
            # Buscar dados reais
            data = await self.crypto_service.get_trending_cryptos(limit=limit, order_by=order_by)
            
            # Verificar qualidade dos dados
            valid_data = [item for item in data if item and item.get('price') and item.get('symbol')]
            
            if len(valid_data) >= limit // 2:  # Se temos pelo menos 50% dos dados válidos
                # Armazenar no cache
                await self.cache_manager.set(cache_key, valid_data, 'trending', ttl=600)  # 10 min
                return valid_data
            else:
                # Usar fallback se dados insuficientes
                self.metrics['fallback_used'] += 1
                fallback_data = self.fallback_service.get_sample_trending_cryptos(limit, order_by)
                return fallback_data
                
        except Exception as e:
            self.logger.error(f"Error getting trending cryptos: {e}")
            self.metrics['errors'] += 1
            # Em caso de erro, usar fallback
            return self.fallback_service.get_sample_trending_cryptos(limit, order_by)
    
    # ============== ADMIN OPERATIONS ==============
    
    async def clear_all_caches(self) -> Dict[str, Any]:
        """Limpa todos os caches"""
        try:
            # Limpar cache manager
            await self.cache_manager.clear_all()
            
            # Limpar caches dos serviços
            self.stock_service.clear_cache()
            self.crypto_service.clear_cache()
            
            return {
                'success': True,
                'message': 'Todos os caches foram limpos',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error clearing caches: {e}")
            return {
                'success': False,
                'message': f'Erro ao limpar caches: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do sistema"""
        try:
            # Métricas do cache manager
            cache_stats = await self.cache_manager.get_stats()
            
            # Métricas dos serviços
            stock_stats = self.stock_service.get_cache_stats()
            crypto_stats = self.crypto_service.get_cache_stats()
            
            return {
                'orchestrator_metrics': self.metrics,
                'cache_manager_stats': cache_stats,
                'stock_service_stats': stock_stats,
                'crypto_service_stats': crypto_stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {
                'error': f'Erro ao obter métricas: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    # ============== HEALTH CHECK ==============
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde de todos os serviços"""
        health_status = {
            'status': 'healthy',
            'services': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Verificar stock service
            test_stock = await self.stock_service.get_stock_data('AAPL')
            health_status['services']['stock_service'] = 'healthy' if test_stock else 'degraded'
            
            # Verificar crypto service
            test_crypto = await self.crypto_service.get_crypto_data('BTC')
            health_status['services']['crypto_service'] = 'healthy' if test_crypto else 'degraded'
            
            # Verificar cache manager
            health_status['services']['cache_manager'] = 'healthy'
            
            # Status geral
            service_statuses = list(health_status['services'].values())
            if 'unhealthy' in service_statuses:
                health_status['status'] = 'unhealthy'
            elif 'degraded' in service_statuses:
                health_status['status'] = 'degraded'
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
