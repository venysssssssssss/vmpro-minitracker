from typing import Dict, List, Optional

from interfaces.data_provider import CryptoDataProvider, DataProvider
from models.stock import Crypto, Stock


class TrackerService:
    """Serviço principal para tracking de ações e criptos - Princípio da Responsabilidade Única"""

    def __init__(
        self, stock_provider: DataProvider, crypto_provider: CryptoDataProvider
    ):
        self.stock_provider = stock_provider
        self.crypto_provider = crypto_provider

    def get_stock_data(self, symbol: str) -> Optional[Stock]:
        """Busca dados de uma ação específica"""
        data = self.stock_provider.get_stock_data(symbol)
        if data:
            return Stock(**data)
        return None

    def get_multiple_stocks(self, symbols: List[str]) -> List[Stock]:
        """Busca dados de múltiplas ações"""
        stocks_data = self.stock_provider.get_multiple_stocks(symbols)
        return [Stock(**data) for data in stocks_data.values()]

    def get_trending_stocks(self, limit: int = 10) -> List[Stock]:
        """Busca ações em alta"""
        trending_data = self.stock_provider.get_trending_stocks(limit)
        return [Stock(**data) for data in trending_data]

    def get_crypto_data(self, symbol: str) -> Optional[Crypto]:
        """Busca dados de uma criptomoeda específica"""
        data = self.crypto_provider.get_crypto_data(symbol)
        if data:
            return Crypto(**data)
        return None

    def get_multiple_cryptos(self, symbols: List[str]) -> List[Crypto]:
        """Busca dados de múltiplas criptomoedas"""
        cryptos_data = self.crypto_provider.get_multiple_cryptos(symbols)
        return [Crypto(**data) for data in cryptos_data.values()]

    def get_trending_cryptos(self, limit: int = 10) -> List[Crypto]:
        """Busca criptomoedas em alta"""
        trending_data = self.crypto_provider.get_trending_cryptos(limit)
        return [Crypto(**data) for data in trending_data]


class PortfolioService:
    """Serviço para gerenciar portfolio do usuário - Princípio da Responsabilidade Única"""

    def __init__(self, tracker_service: TrackerService):
        self.tracker_service = tracker_service
        self.stock_portfolio: Dict[str, dict] = {}
        self.crypto_portfolio: Dict[str, dict] = {}

    def add_stock_to_portfolio(
        self, symbol: str, quantity: float, purchase_price: float
    ):
        """Adiciona uma ação ao portfolio"""
        self.stock_portfolio[symbol.upper()] = {
            'quantity': quantity,
            'purchase_price': purchase_price,
        }

    def add_crypto_to_portfolio(
        self, symbol: str, quantity: float, purchase_price: float
    ):
        """Adiciona uma criptomoeda ao portfolio"""
        self.crypto_portfolio[symbol.upper()] = {
            'quantity': quantity,
            'purchase_price': purchase_price,
        }

    def get_portfolio_summary(self) -> Dict:
        """Retorna resumo do portfolio com P&L"""
        summary = {
            'stocks': [],
            'cryptos': [],
            'total_value': 0,
            'total_invested': 0,
            'total_pnl': 0,
        }

        # Processar ações
        if self.stock_portfolio:
            symbols = list(self.stock_portfolio.keys())
            current_stocks = self.tracker_service.get_multiple_stocks(symbols)

            for stock in current_stocks:
                if stock.symbol in self.stock_portfolio:
                    portfolio_data = self.stock_portfolio[stock.symbol]
                    quantity = portfolio_data['quantity']
                    purchase_price = portfolio_data['purchase_price']

                    current_value = stock.price * quantity
                    invested_value = purchase_price * quantity
                    pnl = current_value - invested_value
                    pnl_percent = (
                        (pnl / invested_value) * 100
                        if invested_value > 0
                        else 0
                    )

                    stock_summary = {
                        **stock.to_dict(),
                        'quantity': quantity,
                        'purchase_price': purchase_price,
                        'current_value': current_value,
                        'invested_value': invested_value,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                    }

                    summary['stocks'].append(stock_summary)
                    summary['total_value'] += current_value
                    summary['total_invested'] += invested_value

        # Processar criptomoedas
        if self.crypto_portfolio:
            symbols = list(self.crypto_portfolio.keys())
            current_cryptos = self.tracker_service.get_multiple_cryptos(
                symbols
            )

            for crypto in current_cryptos:
                if crypto.symbol in self.crypto_portfolio:
                    portfolio_data = self.crypto_portfolio[crypto.symbol]
                    quantity = portfolio_data['quantity']
                    purchase_price = portfolio_data['purchase_price']

                    current_value = crypto.price * quantity
                    invested_value = purchase_price * quantity
                    pnl = current_value - invested_value
                    pnl_percent = (
                        (pnl / invested_value) * 100
                        if invested_value > 0
                        else 0
                    )

                    crypto_summary = {
                        **crypto.to_dict(),
                        'quantity': quantity,
                        'purchase_price': purchase_price,
                        'current_value': current_value,
                        'invested_value': invested_value,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                    }

                    summary['cryptos'].append(crypto_summary)
                    summary['total_value'] += current_value
                    summary['total_invested'] += invested_value

        summary['total_pnl'] = (
            summary['total_value'] - summary['total_invested']
        )

        return summary
