"""
Controladores modernos seguindo princípios SOLID
Separação de responsabilidades entre validação, lógica de negócio e resposta
"""
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, validator
from enum import Enum

from services.service_manager import ServiceManager
from interfaces.service_interfaces import DataSourceStatus


class Region(str, Enum):
    """Enum para regiões suportadas"""
    US = "US"
    BR = "BR"
    ALL = "all"


class CryptoOrderBy(str, Enum):
    """Enum para ordenação de criptomoedas"""
    PERCENT_CHANGE_24H = "percent_change_24h"
    MARKET_CAP = "market_cap"
    VOLUME = "volume"
    PRICE = "price"


class StockRequest(BaseModel):
    """Modelo de validação para requisições de ações"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Símbolo da ação")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class MultipleStocksRequest(BaseModel):
    """Modelo de validação para múltiplas ações"""
    symbols: str = Field(..., description="Símbolos separados por vírgula")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        symbols = [s.strip().upper() for s in v.split(",") if s.strip()]
        if len(symbols) == 0:
            raise ValueError("Pelo menos um símbolo deve ser fornecido")
        if len(symbols) > 20:
            raise ValueError("Máximo de 20 símbolos por vez")
        return ",".join(symbols)


class TrendingStocksRequest(BaseModel):
    """Modelo de validação para ações em alta"""
    limit: int = Field(10, ge=1, le=50, description="Número de ações a retornar")
    region: Region = Field(Region.US, description="Região do mercado")


class CryptoRequest(BaseModel):
    """Modelo de validação para requisições de criptomoedas"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Símbolo da criptomoeda")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class TrendingCryptosRequest(BaseModel):
    """Modelo de validação para criptomoedas em alta"""
    limit: int = Field(10, ge=1, le=50, description="Número de criptomoedas a retornar")
    order_by: CryptoOrderBy = Field(CryptoOrderBy.PERCENT_CHANGE_24H, description="Ordenação")


class BaseController:
    """Controlador base com funcionalidades comuns"""
    
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
    
    def _handle_service_error(self, service_name: str, error: Exception) -> HTTPException:
        """Converte erros de serviço em HTTPException apropriada"""
        error_msg = str(error)
        
        if "Circuit breaker is open" in error_msg:
            return HTTPException(
                status_code=503,
                detail=f"Serviço {service_name} temporariamente indisponível. Tente novamente em alguns minutos."
            )
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            return HTTPException(
                status_code=429,
                detail=f"Muitas requisições para {service_name}. Tente novamente em alguns segundos."
            )
        elif "not found" in error_msg.lower():
            return HTTPException(
                status_code=404,
                detail="Recurso não encontrado"
            )
        else:
            return HTTPException(
                status_code=500,
                detail=f"Erro interno no serviço {service_name}"
            )
    
    async def _check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """Verifica rate limiting por IP e endpoint"""
        key = f"{client_ip}:{endpoint}"
        return await self.service_manager.rate_limiter.is_allowed(key, 60, 60)  # 60 req/min


class StockController(BaseController):
    """Controlador para operações de ações"""
    
    async def get_stock(self, request: StockRequest, client_ip: str) -> Dict[str, Any]:
        """Busca dados de uma ação específica"""
        try:
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "get_stock"):
                raise HTTPException(status_code=429, detail="Rate limit excedido")
            
            data = await self.service_manager.get_stock_data(request.symbol)
            
            if not data:
                raise HTTPException(status_code=404, detail=f"Ação {request.symbol} não encontrada")
            
            return self.service_manager.response_formatter.format_success_response(data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise self._handle_service_error("stock", e)
    
    async def get_multiple_stocks(self, request: MultipleStocksRequest, client_ip: str) -> Dict[str, Any]:
        """Busca dados de múltiplas ações"""
        try:
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "get_multiple_stocks"):
                raise HTTPException(status_code=429, detail="Rate limit excedido")
            
            symbol_list = request.symbols.split(",")
            data = await self.service_manager.stock_service.get_multiple_stocks(symbol_list)
            
            return self.service_manager.response_formatter.format_success_response(data)
            
        except Exception as e:
            raise self._handle_service_error("stock", e)
    
    async def get_trending_stocks(self, request: TrendingStocksRequest, client_ip: str) -> Dict[str, Any]:
        """Busca ações em alta por região"""
        try:
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "get_trending_stocks"):
                raise HTTPException(status_code=429, detail="Rate limit excedido")
            
            data = await self.service_manager.get_trending_stocks(
                region=request.region.value,
                limit=request.limit
            )
            
            return self.service_manager.response_formatter.format_success_response(data)
            
        except Exception as e:
            raise self._handle_service_error("stock", e)


class CryptoController(BaseController):
    """Controlador para operações de criptomoedas"""
    
    async def get_crypto(self, request: CryptoRequest, client_ip: str) -> Dict[str, Any]:
        """Busca dados de uma criptomoeda específica"""
        try:
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "get_crypto"):
                raise HTTPException(status_code=429, detail="Rate limit excedido")
            
            data = await self.service_manager.get_crypto_data(request.symbol)
            
            if not data:
                raise HTTPException(status_code=404, detail=f"Criptomoeda {request.symbol} não encontrada")
            
            return self.service_manager.response_formatter.format_success_response(data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise self._handle_service_error("crypto", e)
    
    async def get_trending_cryptos(self, request: TrendingCryptosRequest, client_ip: str) -> Dict[str, Any]:
        """Busca criptomoedas em alta"""
        try:
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "get_trending_cryptos"):
                raise HTTPException(status_code=429, detail="Rate limit excedido")
            
            data = await self.service_manager.get_trending_cryptos(
                limit=request.limit,
                order_by=request.order_by.value
            )
            
            return self.service_manager.response_formatter.format_success_response(data)
            
        except Exception as e:
            raise self._handle_service_error("crypto", e)


class AdminController(BaseController):
    """Controlador para operações administrativas"""
    
    async def clear_cache(self, client_ip: str) -> Dict[str, Any]:
        """Limpa todos os caches"""
        try:
            # Rate limiting mais restritivo para admin
            if not await self.service_manager.rate_limiter.is_allowed(f"{client_ip}:admin", 10, 60):
                raise HTTPException(status_code=429, detail="Rate limit excedido para operações admin")
            
            results = await self.service_manager.clear_all_caches()
            
            return self.service_manager.response_formatter.format_success_response(
                results,
                "Cache limpo com sucesso"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")
    
    async def get_cache_stats(self, client_ip: str) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        try:
            # Rate limiting
            if not await self.service_manager.rate_limiter.is_allowed(f"{client_ip}:admin", 10, 60):
                raise HTTPException(status_code=429, detail="Rate limit excedido para operações admin")
            
            stats = {
                "service_metrics": self.service_manager.get_service_metrics(),
                "circuit_breakers": self.service_manager.get_circuit_breaker_status()
            }
            
            return self.service_manager.response_formatter.format_success_response(stats)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os serviços"""
        try:
            health_data = await self.service_manager.health_check()
            
            # Determinar status code baseado na saúde
            if health_data["summary"]["overall_healthy"]:
                return self.service_manager.response_formatter.format_success_response(health_data)
            else:
                # Retornar 503 se algum serviço crítico está down
                response = self.service_manager.response_formatter.format_success_response(health_data)
                response["status_code"] = 503
                return response
                
        except Exception as e:
            return self.service_manager.response_formatter.format_error_response(
                f"Erro ao verificar saúde dos serviços: {str(e)}",
                500
            )


class HTMXController(BaseController):
    """Controlador específico para requisições HTMX"""
    
    def __init__(self, service_manager: ServiceManager, templates):
        super().__init__(service_manager)
        self.templates = templates
    
    async def htmx_trending_stocks(
        self,
        request: Request,
        limit: int = 10,
        region: str = "US"
    ):
        """Endpoint HTMX para ações em alta"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "htmx_stocks"):
                return "<div class='error'>Muitas requisições. Tente novamente em alguns segundos.</div>"
            
            stocks = await self.service_manager.get_trending_stocks(
                region=region.upper(),
                limit=min(limit, 20)
            )
            
            # Adicionar flag para indicar se são dados de fallback
            for stock in stocks:
                if stock.get('is_sample_data'):
                    stock['is_fallback'] = True
            
            return self.templates.TemplateResponse(
                "partials/new_stocks_table.html",
                {"request": request, "stocks": stocks, "region": region.upper()}
            )
            
        except Exception as e:
            error_msg = f"Erro ao carregar ações: {str(e)}"
            return f"<div class='error'>{error_msg}</div>"
    
    async def htmx_trending_cryptos(
        self,
        request: Request,
        limit: int = 10,
        order_by: str = "percent_change_24h"
    ):
        """Endpoint HTMX para criptomoedas em alta"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            
            # Rate limiting
            if not await self._check_rate_limit(client_ip, "htmx_cryptos"):
                return "<div class='error'>Muitas requisições. Tente novamente em alguns segundos.</div>"
            
            cryptos = await self.service_manager.get_trending_cryptos(
                limit=min(limit, 20),
                order_by=order_by
            )
            
            # Adicionar flag para indicar se são dados de fallback
            for crypto in cryptos:
                if crypto.get('is_sample_data'):
                    crypto['is_fallback'] = True
            
            return self.templates.TemplateResponse(
                "partials/crypto_table.html",
                {"request": request, "cryptos": cryptos, "order_by": order_by}
            )
            
        except Exception as e:
            error_msg = f"Erro ao carregar criptomoedas: {str(e)}"
            return f"<div class='error'>{error_msg}</div>"
