"""
Service Manager - Gerencia todos os serviços da aplicação
Segue princípios SOLID: Single Responsibility e Dependency Injection
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from interfaces.service_interfaces import (
    IStockService, ICryptoService, ICacheManager, 
    IResponseFormatter, IRateLimiter, IHealthChecker,
    DataSourceStatus
)


@dataclass
class ServiceMetrics:
    """Métricas de um serviço"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    status: DataSourceStatus = DataSourceStatus.AVAILABLE


class ResponseFormatter(IResponseFormatter):
    """Implementação do formatador de resposta"""
    
    def format_success_response(self, data: Any, message: str = None) -> Dict[str, Any]:
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
    
    def format_error_response(self, error: str, status_code: int = 500) -> Dict[str, Any]:
        return {
            "success": False,
            "data": None,
            "message": None,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "message": error,
                "status_code": status_code
            }
        }
    
    def format_validation_error(self, errors: List[str]) -> Dict[str, Any]:
        return {
            "success": False,
            "data": None,
            "message": "Validation failed",
            "timestamp": datetime.now().isoformat(),
            "error": {
                "message": "Validation errors occurred",
                "status_code": 422,
                "details": errors
            }
        }


class MemoryRateLimiter(IRateLimiter):
    """Implementação simples de rate limiter em memória"""
    
    def __init__(self):
        self.requests = {}
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove requisições antigas
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        if len(self.requests[key]) < limit:
            self.requests[key].append(current_time)
            return True
        
        return False
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        current_time = time.time()
        
        if key not in self.requests:
            return limit
        
        # Remove requisições antigas
        valid_requests = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        return max(0, limit - len(valid_requests))
    
    async def reset(self, key: str) -> bool:
        if key in self.requests:
            del self.requests[key]
            return True
        return False


class HealthChecker(IHealthChecker):
    """Verificador de saúde dos serviços"""
    
    def __init__(self):
        self.services: Dict[str, IStockService | ICryptoService] = {}
    
    def register_service(self, service_name: str, service: IStockService | ICryptoService) -> None:
        self.services[service_name] = service
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        if service_name not in self.services:
            return {
                "service": service_name,
                "status": "not_found",
                "healthy": False,
                "timestamp": datetime.now().isoformat()
            }
        
        service = self.services[service_name]
        
        try:
            status = service.get_service_status()
            
            return {
                "service": service_name,
                "status": status.value,
                "healthy": status == DataSourceStatus.AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        results = {}
        healthy_count = 0
        
        for service_name in self.services:
            result = await self.check_service_health(service_name)
            results[service_name] = result
            if result["healthy"]:
                healthy_count += 1
        
        return {
            "services": results,
            "summary": {
                "total_services": len(self.services),
                "healthy_services": healthy_count,
                "overall_healthy": healthy_count == len(self.services)
            },
            "timestamp": datetime.now().isoformat()
        }


class ServiceManager:
    """
    Gerenciador central de serviços - Segue padrão Service Locator
    Responsabilidades:
    - Gerenciar ciclo de vida dos serviços
    - Prover acesso centralizado aos serviços
    - Monitorar performance e saúde
    - Implementar circuit breaker pattern
    """
    
    def __init__(self):
        self._stock_service: Optional[IStockService] = None
        self._crypto_service: Optional[ICryptoService] = None
        self._cache_manager: Optional[ICacheManager] = None
        self._response_formatter: IResponseFormatter = ResponseFormatter()
        self._rate_limiter: IRateLimiter = MemoryRateLimiter()
        self._health_checker: IHealthChecker = HealthChecker()
        
        # Métricas dos serviços
        self._metrics: Dict[str, ServiceMetrics] = {}
        
        # Circuit breaker state
        self._circuit_breakers: Dict[str, Dict] = {}
    
    # Dependency Injection - Setter Methods
    def set_stock_service(self, service: IStockService) -> None:
        self._stock_service = service
        self._health_checker.register_service("stock_service", service)
        self._metrics["stock_service"] = ServiceMetrics()
    
    def set_crypto_service(self, service: ICryptoService) -> None:
        self._crypto_service = service
        self._health_checker.register_service("crypto_service", service)
        self._metrics["crypto_service"] = ServiceMetrics()
    
    def set_cache_manager(self, cache_manager: ICacheManager) -> None:
        self._cache_manager = cache_manager
    
    def set_rate_limiter(self, rate_limiter: IRateLimiter) -> None:
        self._rate_limiter = rate_limiter
    
    # Getters com validação
    @property
    def stock_service(self) -> IStockService:
        if self._stock_service is None:
            raise RuntimeError("Stock service not initialized")
        return self._stock_service
    
    @property
    def crypto_service(self) -> ICryptoService:
        if self._crypto_service is None:
            raise RuntimeError("Crypto service not initialized")
        return self._crypto_service
    
    @property
    def cache_manager(self) -> ICacheManager:
        return self._cache_manager
    
    @property
    def response_formatter(self) -> IResponseFormatter:
        return self._response_formatter
    
    @property
    def rate_limiter(self) -> IRateLimiter:
        return self._rate_limiter
    
    @property
    def health_checker(self) -> IHealthChecker:
        return self._health_checker
    
    # Circuit Breaker Pattern
    async def _execute_with_circuit_breaker(self, service_name: str, operation, *args, **kwargs):
        """Executa operação com circuit breaker"""
        circuit = self._circuit_breakers.get(service_name, {
            "state": "closed",  # closed, open, half_open
            "failure_count": 0,
            "last_failure_time": None,
            "failure_threshold": 5,
            "timeout": 60  # seconds
        })
        
        # Verificar estado do circuit breaker
        if circuit["state"] == "open":
            if time.time() - circuit["last_failure_time"] > circuit["timeout"]:
                circuit["state"] = "half_open"
                circuit["failure_count"] = 0
            else:
                raise Exception(f"Circuit breaker is open for {service_name}")
        
        try:
            start_time = time.time()
            result = await operation(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Sucesso - resetar circuit breaker se estava meio aberto
            if circuit["state"] == "half_open":
                circuit["state"] = "closed"
                circuit["failure_count"] = 0
            
            # Atualizar métricas
            self._update_metrics(service_name, True, execution_time)
            
            self._circuit_breakers[service_name] = circuit
            return result
            
        except Exception as e:
            # Falha - incrementar contador
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = time.time()
            
            if circuit["failure_count"] >= circuit["failure_threshold"]:
                circuit["state"] = "open"
            
            # Atualizar métricas
            self._update_metrics(service_name, False, 0)
            
            self._circuit_breakers[service_name] = circuit
            raise e
    
    def _update_metrics(self, service_name: str, success: bool, execution_time: float):
        """Atualiza métricas do serviço"""
        if service_name not in self._metrics:
            self._metrics[service_name] = ServiceMetrics()
        
        metrics = self._metrics[service_name]
        metrics.total_requests += 1
        metrics.last_request_time = datetime.now()
        
        if success:
            metrics.successful_requests += 1
            # Calcular média móvel do tempo de resposta
            if metrics.avg_response_time == 0:
                metrics.avg_response_time = execution_time
            else:
                metrics.avg_response_time = (metrics.avg_response_time + execution_time) / 2
        else:
            metrics.failed_requests += 1
    
    # Métodos públicos com circuit breaker
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Busca dados de ação com circuit breaker"""
        return await self._execute_with_circuit_breaker(
            "stock_service",
            self.stock_service.get_stock_data,
            symbol
        )
    
    async def get_trending_stocks(self, region: str = "US", limit: int = 10) -> List[Dict[str, Any]]:
        """Busca ações em alta com circuit breaker"""
        return await self._execute_with_circuit_breaker(
            "stock_service",
            self.stock_service.get_trending_stocks,
            limit=limit,
            region=region
        )
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Busca dados de cripto com circuit breaker"""
        return await self._execute_with_circuit_breaker(
            "crypto_service",
            self.crypto_service.get_crypto_data,
            symbol
        )
    
    async def get_trending_cryptos(self, limit: int = 10, order_by: str = "percent_change_24h") -> List[Dict[str, Any]]:
        """Busca criptos em alta com circuit breaker"""
        return await self._execute_with_circuit_breaker(
            "crypto_service",
            self.crypto_service.get_trending_cryptos,
            limit=int(limit),
            order_by=str(order_by)
        )
    
    # Métodos administrativos
    async def clear_all_caches(self) -> Dict[str, bool]:
        """Limpa todos os caches"""
        results = {}
        
        # Limpar cache do stock service
        if self._stock_service:
            results["stock_cache"] = self._stock_service.clear_cache()
        
        # Limpar cache do crypto service
        if self._crypto_service:
            results["crypto_cache"] = self._crypto_service.clear_cache()
        
        # Limpar cache manager se disponível
        if self._cache_manager:
            results["main_cache"] = await self._cache_manager.clear()
        
        return results
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de todos os serviços"""
        return {
            service_name: {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": (
                    metrics.successful_requests / metrics.total_requests * 100
                    if metrics.total_requests > 0 else 0
                ),
                "avg_response_time": metrics.avg_response_time,
                "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                "status": metrics.status.value
            }
            for service_name, metrics in self._metrics.items()
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Retorna status dos circuit breakers"""
        return self._circuit_breakers
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os serviços"""
        return await self._health_checker.check_all_services()
