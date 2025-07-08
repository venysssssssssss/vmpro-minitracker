from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class DataProvider(ABC):
    """Interface para provedores de dados financeiros"""
    
    @abstractmethod
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma ação específica"""
        pass
    
    @abstractmethod
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca dados de múltiplas ações"""
        pass
    
    @abstractmethod
    def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """Busca ações em alta"""
        pass

class CryptoDataProvider(ABC):
    """Interface para provedores de dados de criptomoedas"""
    
    @abstractmethod
    def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de uma criptomoeda específica"""
        pass
    
    @abstractmethod
    def get_multiple_cryptos(self, symbols: List[str]) -> Dict[str, Dict]:
        """Busca dados de múltiplas criptomoedas"""
        pass
    
    @abstractmethod
    def get_trending_cryptos(self, limit: int = 10) -> List[Dict]:
        """Busca criptomoedas em alta"""
        pass