"""
Modelos Pydantic para APIs FastAPI
Modelos otimizados para serialização e validação
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class CurrencyType(str, Enum):
    USD = 'USD'
    BRL = 'BRL'


class RegionType(str, Enum):
    ALL = 'all'
    BR = 'BR'
    US = 'US'


class PeriodType(str, Enum):
    ONE_DAY = '1D'
    FIVE_DAYS = '5D'
    ONE_MONTH = '1M'
    THREE_MONTHS = '3M'
    SIX_MONTHS = '6M'
    NINE_MONTHS = '9M'
    ONE_YEAR = '12M'


# ================================
# MODELOS DE RESPOSTA
# ================================


class StockResponse(BaseModel):
    """Modelo de resposta para dados de ações"""

    symbol: str = Field(..., description='Símbolo da ação')
    name: str = Field(..., description='Nome da empresa')
    price: float = Field(..., description='Preço atual')
    previous_close: float = Field(..., description='Fechamento anterior')
    change_amount: Optional[float] = Field(
        None, description='Mudança em valor absoluto'
    )
    change_percent: Optional[float] = Field(
        None, description='Mudança percentual'
    )
    market_cap: Optional[float] = Field(
        None, description='Capitalização de mercado'
    )
    volume: Optional[int] = Field(None, description='Volume de negociação')
    is_gaining: bool = Field(..., description='Se está em alta')
    last_updated: datetime = Field(..., description='Última atualização')

    @validator('change_amount', pre=True, always=True)
    def calculate_change_amount(cls, v, values):
        if v is None and 'price' in values and 'previous_close' in values:
            return values['price'] - values['previous_close']
        return v

    @validator('change_percent', pre=True, always=True)
    def calculate_change_percent(cls, v, values):
        if v is None and 'price' in values and 'previous_close' in values:
            if values['previous_close'] > 0:
                return (
                    (values['price'] - values['previous_close'])
                    / values['previous_close']
                ) * 100
        return v

    @validator('is_gaining', pre=True, always=True)
    def calculate_is_gaining(cls, v, values):
        if 'change_amount' in values:
            return values['change_amount'] > 0
        if 'price' in values and 'previous_close' in values:
            return values['price'] > values['previous_close']
        return False

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CryptoResponse(BaseModel):
    """Modelo de resposta para dados de criptomoedas"""

    symbol: str = Field(..., description='Símbolo da criptomoeda')
    name: str = Field(..., description='Nome da criptomoeda')
    price: float = Field(..., description='Preço atual')
    previous_close: float = Field(..., description='Preço anterior (24h)')
    change_amount: Optional[float] = Field(
        None, description='Mudança em valor absoluto'
    )
    change_percent_24h: Optional[float] = Field(
        None, description='Mudança percentual 24h'
    )
    market_cap: Optional[float] = Field(
        None, description='Capitalização de mercado'
    )
    volume_24h: Optional[float] = Field(None, description='Volume 24h')
    is_gaining: bool = Field(..., description='Se está em alta')
    last_updated: datetime = Field(..., description='Última atualização')

    @validator('change_amount', pre=True, always=True)
    def calculate_change_amount(cls, v, values):
        if v is None and 'price' in values and 'previous_close' in values:
            return values['price'] - values['previous_close']
        return v

    @validator('change_percent_24h', pre=True, always=True)
    def calculate_change_percent(cls, v, values):
        if v is None and 'price' in values and 'previous_close' in values:
            if values['previous_close'] > 0:
                return (
                    (values['price'] - values['previous_close'])
                    / values['previous_close']
                ) * 100
        return v

    @validator('is_gaining', pre=True, always=True)
    def calculate_is_gaining(cls, v, values):
        if 'change_amount' in values:
            return values['change_amount'] > 0
        if 'price' in values and 'previous_close' in values:
            return values['price'] > values['previous_close']
        return False

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PortfolioItem(BaseModel):
    """Item do portfolio"""

    symbol: str
    quantity: float
    purchase_price: float
    current_price: float
    current_value: float
    invested_value: float
    pnl: float
    pnl_percent: float
    type: str  # 'stock' ou 'crypto'


class PortfolioResponse(BaseModel):
    """Modelo de resposta para portfolio"""

    stocks: List[PortfolioItem] = []
    cryptos: List[PortfolioItem] = []
    total_value: float
    total_invested: float
    total_pnl: float
    total_pnl_percent: float
    last_updated: datetime


# ================================
# MODELOS DE REQUEST
# ================================


class AddToPortfolioRequest(BaseModel):
    """Request para adicionar item ao portfolio"""

    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)


class SearchRequest(BaseModel):
    """Request para busca"""

    query: str = Field(..., min_length=1, max_length=50)
    type: Optional[str] = Field('all', pattern='^(all|stocks|cryptos)$')
    limit: Optional[int] = Field(10, ge=1, le=50)


# ================================
# MODELOS DE RESPOSTA GENÉRICA
# ================================


class APIResponse(BaseModel):
    """Resposta padrão da API"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchResponse(BaseModel):
    """Resposta para operações em lote"""

    success: bool
    data: List[Any]
    count: int
    symbols_requested: List[str]
    symbols_found: List[str]
    symbols_not_found: List[str]
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Resposta do health check"""

    status: str
    timestamp: datetime
    cache: Dict[str, Any]
    apis: Dict[str, Any]
    version: str


class MetricsResponse(BaseModel):
    """Resposta das métricas"""

    performance: Dict[str, Any]
    cache: Dict[str, Any]
    timestamp: datetime


# ================================
# MODELOS DE CONFIGURAÇÃO
# ================================


class FilterOptions(BaseModel):
    """Opções de filtro disponíveis"""

    regions: List[str]
    currencies: List[str]
    periods: List[str]
    languages: List[str]


class ConfigResponse(BaseModel):
    """Configurações do sistema"""

    use_mock_data: bool
    refresh_interval: int
    max_trending_items: int
    supported_currencies: List[str]
    supported_regions: List[str]
    supported_periods: List[str]
    version: str
    filters: FilterOptions
