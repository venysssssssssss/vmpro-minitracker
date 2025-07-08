"""
Interfaces para serviços - Seguindo princípio da Inversão de Dependência (SOLID)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum


class CacheStrategy(Enum):
    """Estratégias de cache disponíveis"""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"


class DataSourceStatus(Enum):
    """Status das fontes de dados"""
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    FALLBACK = "fallback"


class IDataService(ABC):
    """Interface base para serviços de dados"""
    
    @abstractmethod
    async def get_data(self, identifier: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Busca dados por identificador"""
        pass
    
    @abstractmethod
    async def get_multiple_data(self, identifiers: List[str], **kwargs) -> Dict[str, Dict[str, Any]]:
        """Busca múltiplos dados"""
        pass
    
    @abstractmethod
    async def get_trending_data(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Busca dados em tendência"""
        pass
    
    @abstractmethod
    def get_service_status(self) -> DataSourceStatus:
        """Retorna status do serviço"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> bool:
        """Limpa cache do serviço"""
        pass


class IStockService(IDataService):
    """Interface específica para serviços de ações"""
    
    @abstractmethod
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Busca dados de uma ação"""
        pass
    
    @abstractmethod
    async def get_trending_stocks(self, region: str = "US", limit: int = 10) -> List[Dict[str, Any]]:
        """Busca ações em alta por região"""
        pass
    
    @abstractmethod
    async def get_market_overview(self, region: str = "US") -> Dict[str, Any]:
        """Retorna visão geral do mercado"""
        pass


class ICryptoService(IDataService):
    """Interface específica para serviços de criptomoedas"""
    
    @abstractmethod
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Busca dados de uma criptomoeda"""
        pass
    
    @abstractmethod
    async def get_trending_cryptos(self, limit: int = 10, order_by: str = "percent_change_24h") -> List[Dict[str, Any]]:
        """Busca criptomoedas em alta"""
        pass


class ICacheManager(ABC):
    """Interface para gerenciadores de cache"""
    
    @abstractmethod
    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Busca item no cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300, category: str = "default") -> bool:
        """Armazena item no cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str, category: str = "default") -> bool:
        """Remove item do cache"""
        pass
    
    @abstractmethod
    async def clear(self, category: Optional[str] = None) -> bool:
        """Limpa cache por categoria ou total"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        pass


class IResponseFormatter(ABC):
    """Interface para formatadores de resposta"""
    
    @abstractmethod
    def format_success_response(self, data: Any, message: str = None) -> Dict[str, Any]:
        """Formata resposta de sucesso"""
        pass
    
    @abstractmethod
    def format_error_response(self, error: str, status_code: int = 500) -> Dict[str, Any]:
        """Formata resposta de erro"""
        pass
    
    @abstractmethod
    def format_validation_error(self, errors: List[str]) -> Dict[str, Any]:
        """Formata erro de validação"""
        pass


class IRateLimiter(ABC):
    """Interface para limitador de taxa"""
    
    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Verifica se requisição é permitida"""
        pass
    
    @abstractmethod
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """Retorna requisições restantes"""
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> bool:
        """Reseta contador para uma chave"""
        pass


class IHealthChecker(ABC):
    """Interface para verificação de saúde dos serviços"""
    
    @abstractmethod
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Verifica saúde de um serviço específico"""
        pass
    
    @abstractmethod
    async def check_all_services(self) -> Dict[str, Any]:
        """Verifica saúde de todos os serviços"""
        pass
    
    @abstractmethod
    def register_service(self, service_name: str, service: IDataService) -> None:
        """Registra um serviço para monitoramento"""
        pass
