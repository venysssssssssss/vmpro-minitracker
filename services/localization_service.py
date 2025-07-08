# filepath: /home/synev1/dev/vmpro/app/stock-tracker/src/services/localization_service.py
from typing import Dict, Any
import requests
import requests_cache
from datetime import datetime
from utils.config import Config
import json

# Cache para conversão de moedas
requests_cache.install_cache('currency_cache', expire_after=3600)  # 1 hora

class CurrencyService:
    """Serviço para conversão de moedas"""
    
    def __init__(self):
        self.exchange_rates = getattr(Config, 'EXCHANGE_RATES', {'USD_TO_BRL': 5.20, 'BRL_TO_USD': 0.19})
        # Taxa de câmbio USD para BRL (será atualizada via API)
        self.exchange_rate_usd_brl = 5.20  # Taxa padrão
        
    def update_exchange_rate(self):
        """Atualiza taxa de câmbio via API externa"""
        try:
            # Usando API gratuita para taxas de câmbio
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.exchange_rate_usd_brl = data['rates'].get('BRL', self.exchange_rate_usd_brl)
                print(f"Taxa de câmbio atualizada: 1 USD = {self.exchange_rate_usd_brl} BRL")
        except Exception as e:
            print(f"Erro ao atualizar taxa de câmbio: {e}")
    
    def convert_price(self, price: float, from_currency: str, to_currency: str) -> float:
        """Converte preço entre moedas"""
        if from_currency == to_currency:
            return price
        
        if from_currency == 'USD' and to_currency == 'BRL':
            return price * self.exchange_rate_usd_brl
        elif from_currency == 'BRL' and to_currency == 'USD':
            return price / self.exchange_rate_usd_brl
        
        return price  # Fallback
    
    def format_currency(self, amount: float, currency: str) -> str:
        """Formata valor com símbolo da moeda"""
        if currency == 'BRL':
            return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:  # USD
            return f"${amount:,.2f}"
    
    def get_currency_symbol(self, currency: str) -> str:
        """Retorna símbolo da moeda"""
        symbols = {
            'USD': '$',
            'BRL': 'R$'
        }
        return symbols.get(currency, '$')

class TranslationService:
    """Serviço para tradução e internacionalização"""
    
    def __init__(self):
        self.translations = {
            'pt-BR': {
                # Interface
                'dashboard_title': 'Mini Tracker - Ações & Cripto',
                'trending_stocks': 'Ações em Alta',
                'trending_cryptos': 'Criptos em Alta',
                'my_portfolio': 'Meu Portfolio',
                'market_status': 'Status do Mercado',
                'search_stock': 'Buscar Ação',
                'search_crypto': 'Buscar Cripto',
                'add_to_portfolio': 'Adicionar ao Portfolio',
                
                # Dados
                'price': 'Preço',
                'change': 'Variação',
                'volume': 'Volume',
                'market_cap': 'Cap. Mercado',
                'total_value': 'Valor Total',
                'invested': 'Investido',
                'profit_loss': 'Lucro/Prejuízo',
                'percentage': 'Percentual',
                
                # Períodos
                '1D': '1 Dia',
                '5D': '5 Dias', 
                '1M': '1 Mês',
                '3M': '3 Meses',
                '6M': '6 Meses',
                '9M': '9 Meses',
                '12M': '12 Meses',
                
                # Estados
                'market_open': 'Mercado Aberto',
                'market_closed': 'Mercado Fechado',
                'loading': 'Carregando...',
                'error': 'Erro',
                'no_data': 'Sem dados disponíveis',
                
                # Ações
                'brazilian_stocks': 'Ações Brasileiras',
                'us_stocks': 'Ações Americanas',
                'all_stocks': 'Todas as Ações',
                
                # Filtros
                'filter_by_period': 'Filtrar por Período',
                'filter_by_region': 'Filtrar por Região',
                'currency': 'Moeda',
                'language': 'Idioma',
                'filters': 'Filtros',
                'period': 'Período',
                'region': 'Região',
                'all_regions': 'Todas as Regiões'
            },
            'en-US': {
                # Interface
                'dashboard_title': 'Mini Tracker - Stocks & Crypto',
                'trending_stocks': 'Trending Stocks',
                'trending_cryptos': 'Trending Cryptos',
                'my_portfolio': 'My Portfolio',
                'market_status': 'Market Status',
                'search_stock': 'Search Stock',
                'search_crypto': 'Search Crypto',
                'add_to_portfolio': 'Add to Portfolio',
                
                # Data
                'price': 'Price',
                'change': 'Change',
                'volume': 'Volume',
                'market_cap': 'Market Cap',
                'total_value': 'Total Value',
                'invested': 'Invested',
                'profit_loss': 'Profit/Loss',
                'percentage': 'Percentage',
                
                # Periods
                '1D': '1 Day',
                '5D': '5 Days',
                '1M': '1 Month',
                '3M': '3 Months',
                '6M': '6 Months',
                '9M': '9 Months',
                '12M': '12 Months',
                
                # States
                'market_open': 'Market Open',
                'market_closed': 'Market Closed',
                'loading': 'Loading...',
                'error': 'Error',
                'no_data': 'No data available',
                
                # Stocks
                'brazilian_stocks': 'Brazilian Stocks',
                'us_stocks': 'US Stocks',
                'all_stocks': 'All Stocks',
                
                # Filters
                'filter_by_period': 'Filter by Period',
                'filter_by_region': 'Filter by Region',
                'currency': 'Currency',
                'language': 'Language',
                'filters': 'Filters',
                'period': 'Period',
                'region': 'Region',
                'all_regions': 'All Regions'
            }
        }
    
    def get_translation(self, key: str, language: str = 'pt-BR') -> str:
        """Retorna tradução para uma chave"""
        return self.translations.get(language, {}).get(key, key)
    
    def get_all_translations(self, language: str = 'pt-BR') -> Dict[str, str]:
        """Retorna todas as traduções para um idioma"""
        return self.translations.get(language, {})

class LocalizationService:
    """Serviço principal de localização - sem dependência circular"""
    
    def __init__(self):
        self.currency_service = CurrencyService()
        self.translation_service = TranslationService()
        # Inicializar taxa de câmbio
        self.currency_service.update_exchange_rate()
    
    def get_available_currencies(self) -> list:
        """Retorna lista de moedas disponíveis"""
        return [
            {'value': 'USD', 'label': 'USD - US Dollar', 'flag': '🇺🇸'},
            {'value': 'BRL', 'label': 'BRL - Real Brasileiro', 'flag': '🇧🇷'}
        ]
    
    def get_available_languages(self) -> list:
        """Retorna lista de idiomas disponíveis"""
        return [
            {'value': 'pt-BR', 'label': 'Português', 'flag': '🇧🇷'},
            {'value': 'en-US', 'label': 'English', 'flag': '🇺🇸'}
        ]
    
    def get_available_regions(self) -> list:
        """Retorna lista de regiões disponíveis"""
        return [
            {'value': 'all', 'label': 'Todas as Regiões'},
            {'value': 'BR', 'label': 'Brasil', 'flag': '🇧🇷'},
            {'value': 'US', 'label': 'Estados Unidos', 'flag': '🇺🇸'}
        ]
    
    def get_available_periods(self) -> list:
        """Retorna lista de períodos disponíveis"""
        return [
            {'value': '1D', 'label': '1 Dia'},
            {'value': '5D', 'label': '5 Dias'},
            {'value': '1M', 'label': '1 Mês'},
            {'value': '3M', 'label': '3 Meses'},
            {'value': '6M', 'label': '6 Meses'},
            {'value': '9M', 'label': '9 Meses'},
            {'value': '12M', 'label': '12 Meses'}
        ]
    
    def translate(self, text: str, language: str = 'pt-BR') -> str:
        """Traduz um texto para o idioma especificado"""
        return self.translation_service.get_translation(text, language)
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Converte valor entre moedas"""
        return self.currency_service.convert_price(amount, from_currency, to_currency)
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Retorna taxa de câmbio entre duas moedas"""
        if from_currency == to_currency:
            return 1.0
        
        if from_currency == 'USD' and to_currency == 'BRL':
            return self.currency_service.exchange_rate_usd_brl
        elif from_currency == 'BRL' and to_currency == 'USD':
            return 1.0 / self.currency_service.exchange_rate_usd_brl
        
        return 1.0  # Fallback
    
    def format_currency(self, amount: float, currency: str = 'USD') -> str:
        """Formata valor monetário de acordo com a moeda"""
        return self.currency_service.format_currency(amount, currency)
    
    def localize_stock_data(self, stock_data: Dict, target_currency: str = 'USD', language: str = 'pt-BR') -> Dict:
        """Localiza dados de ação"""
        localized_data = stock_data.copy()
        
        # Converter moedas
        if 'price' in localized_data:
            localized_data['price'] = self.currency_service.convert_price(
                localized_data['price'], 'USD', target_currency
            )
            localized_data['formatted_price'] = self.currency_service.format_currency(
                localized_data['price'], target_currency
            )
        
        if 'previous_close' in localized_data:
            localized_data['previous_close'] = self.currency_service.convert_price(
                localized_data['previous_close'], 'USD', target_currency
            )
        
        if 'market_cap' in localized_data and localized_data['market_cap']:
            localized_data['market_cap'] = self.currency_service.convert_price(
                localized_data['market_cap'], 'USD', target_currency
            )
        
        # Adicionar traduções
        localized_data['currency'] = target_currency
        localized_data['language'] = language
        
        return localized_data
    
    def get_region_from_symbol(self, symbol: str) -> str:
        """Identifica região da ação pelo símbolo"""
        if '.SA' in symbol:
            return 'BR'
        else:
            return 'US'

class StockRegionService:
    """Serviço para gerenciar ações por região"""
    
    def __init__(self):
        self.stock_lists = {
            'brazil': [
                'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
                'WEGE3.SA', 'MGLU3.SA', 'B3SA3.SA', 'SUZB3.SA', 'RENT3.SA',
                'LREN3.SA', 'JBSS3.SA', 'CCRO3.SA', 'RAIL3.SA', 'GGBR4.SA',
                'USIM5.SA', 'CSNA3.SA', 'EMBR3.SA', 'CIEL3.SA', 'HAPV3.SA'
            ],
            'usa': [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'V', 'JPM', 'UNH', 'PG', 'HD', 'BAC', 'ABBV', 'KO', 'PFE',
                'AVGO', 'CRM', 'TMO', 'WMT', 'DIS', 'ADBE', 'CSCO', 'INTC'
            ]
        }
        
        self.stock_names = {
            # Ações brasileiras
            'PETR4.SA': 'Petrobras',
            'VALE3.SA': 'Vale',
            'ITUB4.SA': 'Itaú Unibanco',
            'BBDC4.SA': 'Bradesco',
            'ABEV3.SA': 'Ambev',
            'WEGE3.SA': 'WEG',
            'MGLU3.SA': 'Magazine Luiza',
            'B3SA3.SA': 'B3',
            'SUZB3.SA': 'Suzano',
            'RENT3.SA': 'Localiza',
            'LREN3.SA': 'Lojas Renner',
            'JBSS3.SA': 'JBS',
            'CCRO3.SA': 'CCR',
            'RAIL3.SA': 'Rumo',
            'GGBR4.SA': 'Gerdau',
            'USIM5.SA': 'Usiminas',
            'CSNA3.SA': 'CSN',
            'EMBR3.SA': 'Embraer',
            'CIEL3.SA': 'Cielo',
            'HAPV3.SA': 'Hapvida',
            
            # Ações americanas
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft',
            'GOOGL': 'Alphabet',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'NVDA': 'NVIDIA',
            'META': 'Meta',
            'NFLX': 'Netflix',
            'V': 'Visa',
            'JPM': 'JPMorgan Chase',
            'UNH': 'UnitedHealth',
            'PG': 'Procter & Gamble',
            'HD': 'Home Depot',
            'BAC': 'Bank of America',
            'ABBV': 'AbbVie',
            'KO': 'Coca-Cola',
            'PFE': 'Pfizer',
            'AVGO': 'Broadcom',
            'CRM': 'Salesforce',
            'TMO': 'Thermo Fisher',
            'WMT': 'Walmart',
            'DIS': 'Disney',
            'ADBE': 'Adobe',
            'CSCO': 'Cisco',
            'INTC': 'Intel'
        }
    
    def get_stocks_by_region(self, region: str) -> list:
        """Retorna lista de ações por região"""
        return self.stock_lists.get(region, [])
    
    def get_stock_name(self, symbol: str) -> str:
        """Retorna nome da empresa pelo símbolo"""
        return self.stock_names.get(symbol, symbol)
    
    def get_all_regions(self) -> list:
        """Retorna todas as regiões disponíveis"""
        return list(self.stock_lists.keys())

class PeriodFilterService:
    """Serviço para filtros de período"""
    
    @staticmethod
    def get_period_options() -> Dict[str, Dict]:
        """Retorna opções de período disponíveis"""
        return {
            '3m': {'months': 3, 'days': 90, 'label': '3 Meses'},
            '6m': {'months': 6, 'days': 180, 'label': '6 Meses'},
            '9m': {'months': 9, 'days': 270, 'label': '9 Meses'},
            '12m': {'months': 12, 'days': 365, 'label': '12 Meses'}
        }
    
    @staticmethod
    def get_yfinance_period(period_key: str) -> str:
        """Converte período para formato do yfinance"""
        period_map = {
            '3m': '3mo',
            '6m': '6mo', 
            '9m': '9mo',
            '12m': '1y'
        }
        return period_map.get(period_key, '3mo')
    
    @staticmethod
    def calculate_period_performance(historical_data, period_days: int) -> Dict:
        """Calcula performance para um período específico"""
        if len(historical_data) < period_days:
            return {'error': 'Dados insuficientes'}
        
        current_price = historical_data[-1]
        period_start_price = historical_data[-period_days]
        
        change = current_price - period_start_price
        change_percent = (change / period_start_price) * 100 if period_start_price > 0 else 0
        
        return {
            'start_price': period_start_price,
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'is_gaining': change > 0
        }
