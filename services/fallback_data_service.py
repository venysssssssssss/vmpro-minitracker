"""
Serviço de dados de fallback para quando APIs externas falham
"""
from datetime import datetime
import random
from typing import Dict, List


class FallbackDataService:
    """Fornece dados de exemplo quando APIs externas falham"""
    
    @staticmethod
    def get_sample_stock_data(symbol: str) -> Dict:
        """Retorna dados de exemplo para uma ação"""
        # Mapeamento de símbolos para nomes reais de empresas
        company_names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'META': 'Meta Platforms Inc.',
            'NFLX': 'Netflix Inc.',
            'V': 'Visa Inc.',
            'JPM': 'JPMorgan Chase & Co.',
            'UNH': 'UnitedHealth Group Inc.',
            'HD': 'The Home Depot Inc.',
            'PG': 'Procter & Gamble Co.',
            'JNJ': 'Johnson & Johnson',
            'MA': 'Mastercard Inc.',
            'VALE3.SA': 'Vale S.A.',
            'PETR4.SA': 'Petróleo Brasileiro S.A.',
            'ITUB4.SA': 'Itaú Unibanco Holding S.A.',
            'BBDC4.SA': 'Banco Bradesco S.A.',
            'ABEV3.SA': 'Ambev S.A.',
            'WEGE3.SA': 'WEG S.A.',
            'RENT3.SA': 'Localiza Rent a Car S.A.',
            'MGLU3.SA': 'Magazine Luiza S.A.',
            'B3SA3.SA': 'B3 S.A.',
            'SUZB3.SA': 'Suzano S.A.',
        }
        
        # Gerar dados aleatórios mas realistas
        base_price = random.uniform(50, 500)
        change_percent = random.uniform(-5, 5)
        change_amount = base_price * (change_percent / 100)
        
        return {
            'symbol': symbol.upper(),
            'name': company_names.get(symbol.upper(), f'{symbol.upper()} Corporation'),
            'price': round(base_price, 2),
            'previous_close': round(base_price - change_amount, 2),
            'change_amount': round(change_amount, 2),
            'change_percent': round(change_percent, 2),
            'market_cap': random.randint(1000000000, 1000000000000),
            'volume': random.randint(1000000, 100000000),
            'sma_5': round(base_price * random.uniform(0.95, 1.05), 2),
            'volatility': round(random.uniform(1, 10), 2),
            'currency': 'USD' if not symbol.endswith('.SA') else 'BRL',
            'exchange': 'NYSE' if not symbol.endswith('.SA') else 'BOVESPA',
            'sector': 'Technology',
            'industry': 'Software',
            'last_updated': datetime.now().isoformat(),
            'is_sample_data': True  # Flag para indicar que são dados de exemplo
        }
    
    @staticmethod
    def get_sample_crypto_data(symbol: str) -> Dict:
        """Retorna dados de exemplo para uma criptomoeda"""
        # Mapeamento de símbolos para nomes reais
        crypto_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'BNB',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'MATIC': 'Polygon',
            'DOT': 'Polkadot',
            'AVAX': 'Avalanche',
            'LINK': 'Chainlink',
            'UNI': 'Uniswap',
            'LTC': 'Litecoin',
            'ATOM': 'Cosmos',
            'FIL': 'Filecoin'
        }
        
        # Gerar dados aleatórios mas realistas para cripto
        base_price = random.uniform(0.01, 50000)
        change_percent = random.uniform(-10, 10)
        
        return {
            'symbol': symbol.upper(),
            'name': crypto_names.get(symbol.upper(), f'{symbol.upper()} Token'),
            'price': round(base_price, 2),
            'change_percent': round(change_percent, 2),
            'change_amount': round(base_price * (change_percent / 100), 2),
            'market_cap': random.randint(100000000, 500000000000),
            'volume': random.randint(10000000, 10000000000),
            'rank': random.randint(1, 100),
            'last_updated': datetime.now().isoformat(),
            'is_sample_data': True  # Flag para indicar que são dados de exemplo
        }
    
    @staticmethod
    def get_sample_trending_stocks(region: str = 'US', limit: int = 10) -> List[Dict]:
        """Retorna dados de exemplo para ações em alta"""
        if region.upper() == 'BR':
            symbols = ['VALE3.SA', 'PETR4.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA']
        else:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        # Gerar mais símbolos se necessário
        while len(symbols) < limit:
            symbols.append(f'STOCK{len(symbols)}')
        
        stocks = []
        for symbol in symbols[:limit]:
            stock_data = FallbackDataService.get_sample_stock_data(symbol)
            # Garantir que seja uma mudança positiva para "trending"
            stock_data['change_percent'] = abs(stock_data['change_percent'])
            stock_data['change_amount'] = abs(stock_data['change_amount'])
            stocks.append(stock_data)
        
        # Ordenar por mudança percentual
        stocks.sort(key=lambda x: x['change_percent'], reverse=True)
        return stocks
    
    @staticmethod
    def get_sample_trending_cryptos(limit: int = 10, order_by: str = 'percent_change_24h') -> List[Dict]:
        """Retorna dados de exemplo para criptomoedas em alta"""
        symbols = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'MATIC', 'DOT', 'AVAX']
        
        # Gerar mais símbolos se necessário
        while len(symbols) < limit:
            symbols.append(f'COIN{len(symbols)}')
        
        cryptos = []
        for symbol in symbols[:limit]:
            crypto_data = FallbackDataService.get_sample_crypto_data(symbol)
            # Garantir que seja uma mudança positiva para "trending"
            crypto_data['change_percent'] = abs(crypto_data['change_percent'])
            crypto_data['change_amount'] = abs(crypto_data['change_amount'])
            cryptos.append(crypto_data)
        
        # Ordenar baseado no parâmetro order_by
        if order_by == 'market_cap':
            cryptos.sort(key=lambda x: x['market_cap'], reverse=True)
        elif order_by == 'volume':
            cryptos.sort(key=lambda x: x['volume'], reverse=True)
        elif order_by == 'price':
            cryptos.sort(key=lambda x: x['price'], reverse=True)
        else:  # percent_change_24h
            cryptos.sort(key=lambda x: x['change_percent'], reverse=True)
        
        return cryptos
