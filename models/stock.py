from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Stock:
    """Modelo para representar uma ação"""

    symbol: str
    name: str
    price: float
    previous_close: float
    market_cap: Optional[float] = None
    volume: Optional[int] = None
    change_percent: Optional[float] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

        if self.change_percent is None and self.previous_close > 0:
            self.change_percent = (
                (self.price - self.previous_close) / self.previous_close
            ) * 100

    @property
    def change_amount(self) -> float:
        """Retorna a mudança em valor absoluto"""
        return self.price - self.previous_close

    @property
    def is_gaining(self) -> bool:
        """Verifica se a ação está em alta"""
        return self.change_amount > 0

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'previous_close': self.previous_close,
            'market_cap': self.market_cap,
            'volume': self.volume,
            'change_percent': self.change_percent,
            'change_amount': self.change_amount,
            'is_gaining': self.is_gaining,
            'last_updated': self.last_updated.isoformat()
            if self.last_updated
            else None,
        }


@dataclass
class Crypto:
    """Modelo para representar uma criptomoeda"""

    symbol: str
    name: str
    price: float
    previous_close: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

        if self.change_percent_24h is None and self.previous_close > 0:
            self.change_percent_24h = (
                (self.price - self.previous_close) / self.previous_close
            ) * 100

    @property
    def change_amount(self) -> float:
        """Retorna a mudança em valor absoluto"""
        return self.price - self.previous_close

    @property
    def is_gaining(self) -> bool:
        """Verifica se a crypto está em alta"""
        return self.change_amount > 0

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'previous_close': self.previous_close,
            'market_cap': self.market_cap,
            'volume_24h': self.volume_24h,
            'change_percent_24h': self.change_percent_24h,
            'change_amount': self.change_amount,
            'is_gaining': self.is_gaining,
            'last_updated': self.last_updated.isoformat()
            if self.last_updated
            else None,
        }
