import os
from typing import Dict, Any

class Config:
    """Configurações da aplicação"""
    
    # APIs - Configurar para usar dados reais
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'  # Mudado para false por padrão
    
    # Yahoo Finance
    YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    # CoinGecko
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Default symbols to track - Ações Brasileiras e Americanas
    BRAZILIAN_STOCKS = ['VALE3.SA', 'PETR4.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'WEGE3.SA', 'RENT3.SA', 'MGLU3.SA', 'B3SA3.SA', 'SUZB3.SA']
    US_STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'JPM', 'V']
    DEFAULT_STOCKS_BR = BRAZILIAN_STOCKS  # Para compatibilidade
    DEFAULT_STOCKS_US = US_STOCKS  # Para compatibilidade
    DEFAULT_STOCKS = BRAZILIAN_STOCKS + US_STOCKS
    DEFAULT_CRYPTOS = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'BNB', 'XRP', 'MATIC', 'SOL', 'AVAX']
    
    # Dashboard settings
    MAX_TRENDING_ITEMS = 15
    REFRESH_INTERVAL_SECONDS = 300  # 5 minutos
    
    # Filtros temporais
    TIME_PERIODS = {
        '3M': '3mo',
        '6M': '6mo', 
        '9M': '9mo',
        '12M': '1y',
        '1D': '1d',
        '5D': '5d',
        '1M': '1mo'
    }
    
    # Configurações de moeda e idioma
    SUPPORTED_CURRENCIES = ['USD', 'BRL']
    SUPPORTED_LANGUAGES = ['pt-BR', 'en-US']
    DEFAULT_CURRENCY = 'USD'
    DEFAULT_LANGUAGE = 'pt-BR'
    
    # Taxa de câmbio (simplificada - em produção usar API real)
    EXCHANGE_RATES = {
        'USD_TO_BRL': 5.20,  # Simulado
        'BRL_TO_USD': 0.19   # Simulado
    }
    
    # Rate limiting
    API_RATE_LIMIT = 60  # requests per minute
    
    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

def get_config() -> Dict[str, Any]:
    """Retorna todas as configurações como dicionário"""
    return {
        'use_mock_data': Config.USE_MOCK_DATA,
        'default_stocks': Config.DEFAULT_STOCKS,
        'default_cryptos': Config.DEFAULT_CRYPTOS,
        'max_trending_items': Config.MAX_TRENDING_ITEMS,
        'refresh_interval': Config.REFRESH_INTERVAL_SECONDS,
        'flask': {
            'host': Config.FLASK_HOST,
            'port': Config.FLASK_PORT,
            'debug': Config.FLASK_DEBUG
        }
    }