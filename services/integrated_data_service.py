import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime
from models.stock import Stock
from utils.config import Config
from services.localization_service import LocalizationService, StockRegionService, PeriodFilterService, CurrencyService

class IntegratedStockService:
    """Serviço integrado de dados de ações com filtros de região, período e localização"""
    
    def __init__(self):
        self.localization_service = LocalizationService()
        self.region_service = StockRegionService()
        self.period_service = PeriodFilterService()
        self.currency_service = CurrencyService()
        
        # Atualizar taxa de câmbio
        try:
            self.localization_service.update_exchange_rate()
        except Exception as e:
            print(f"Erro ao atualizar taxa de câmbio: {e}")
    
    def get_stock_data_with_filters(self, symbol: str, period: str = '3m', currency: str = 'USD') -> Optional[Dict]:
        """Busca dados de uma ação com filtros aplicados"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Obter informações básicas
            info = ticker.info
            
            # Obter histórico baseado no período
            yf_period = self.period_service.get_yfinance_period(period)
            hist = ticker.history(period=yf_period)
            
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            current_volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else None
            
            # Calcular performance do período
            period_data = self.period_service.get_period_options().get(period, {})
            period_days = period_data.get('days', 90)
            
            if len(hist) >= period_days:
                period_start_price = float(hist['Close'].iloc[-period_days])
                period_change = current_price - period_start_price
                period_change_percent = (period_change / period_start_price) * 100 if period_start_price > 0 else 0
            else:
                period_start_price = previous_close
                period_change = current_price - previous_close
                period_change_percent = (period_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Converter moeda se necessário
            if currency == 'BRL':
                current_price = self.currency_service.convert_price(current_price, 'USD', 'BRL')
                previous_close = self.currency_service.convert_price(previous_close, 'USD', 'BRL')
                period_start_price = self.currency_service.convert_price(period_start_price, 'USD', 'BRL')
                period_change = current_price - period_start_price
            
            # Obter nome da empresa
            company_name = self.region_service.get_stock_name(symbol)
            if company_name == symbol:
                company_name = info.get('longName', info.get('shortName', symbol))
            
            return {
                'symbol': symbol.upper(),
                'name': company_name,
                'price': current_price,
                'previous_close': previous_close,
                'market_cap': info.get('marketCap'),
                'volume': current_volume,
                'period': period,
                'period_start_price': period_start_price,
                'period_change': period_change,
                'period_change_percent': period_change_percent,
                'currency': currency,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            print(f"Erro ao buscar dados para {symbol}: {e}")
            return None
    
    def get_stock_data(self, symbol: str, period: str = '1D', currency: str = 'USD', language: str = 'pt-BR') -> Optional[Stock]:
        """Busca dados de uma ação específica com filtros"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Obter informações básicas
            info = ticker.info
            
            # Mapear período para yfinance
            yf_period = self._map_period(period)
            
            # Obter histórico
            hist = ticker.history(period=yf_period)
            
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            current_volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else None
            
            # Dados básicos
            stock_data = {
                'symbol': symbol.upper(),
                'name': info.get('longName', info.get('shortName', symbol.upper())),
                'price': current_price,
                'previous_close': previous_close,
                'market_cap': info.get('marketCap'),
                'volume': current_volume,
                'last_updated': datetime.now()
            }
            
            # Localizar dados
            localized_data = self.localization_service.localize_stock_data(
                stock_data, currency, language
            )
            
            # Remover campos que não são aceitos pelo modelo Stock
            stock_fields = ['symbol', 'name', 'price', 'previous_close', 'market_cap', 'volume', 'change_percent', 'last_updated']
            filtered_data = {k: v for k, v in localized_data.items() if k in stock_fields}
            
            return Stock(**filtered_data)
            
        except Exception as e:
            print(f"Erro ao buscar dados para {symbol}: {e}")
            return None
    
    def get_trending_stocks(self, region: str = 'all', period: str = '1D', currency: str = 'USD', language: str = 'pt-BR', limit: int = 10) -> List[Stock]:
        """Retorna lista de ações em alta com filtros"""
        try:
            # Selecionar símbolos baseado na região
            if region == 'BR':
                symbols = Config.BRAZILIAN_STOCKS
            elif region == 'US':
                symbols = Config.US_STOCKS
            else:  # 'all'
                symbols = Config.BRAZILIAN_STOCKS + Config.US_STOCKS
            
            stocks = []
            
            for symbol in symbols:
                stock = self.get_stock_data(symbol, period, currency, language)
                if stock:
                    stocks.append(stock)
            
            # Ordenar por variação percentual (maior primeiro)
            stocks.sort(key=lambda x: x.change_percent or 0, reverse=True)
            
            return stocks[:limit]
        except Exception as e:
            print(f"Erro ao obter ações em alta: {e}")
            return []
    
    def get_trending_stocks_with_filters(self, region: str = 'all', period: str = '1D', currency: str = 'USD', language: str = 'pt-BR', limit: int = 10) -> Dict:
        """Retorna lista de ações em alta com filtros e metadados"""
        try:
            stocks = self.get_trending_stocks(region, period, currency, language, limit)
            
            filters_applied = {
                'region': region,
                'period': period,
                'currency': currency,
                'language': language
            }
            
            result = {
                'stocks': stocks,
                'filters': filters_applied,
                'total_count': len(stocks)
            }
            
            # Adicionar taxa de câmbio se BRL
            if currency == 'BRL':
                result['exchange_rate'] = self.localization_service.get_exchange_rate('USD', 'BRL')
            
            # Adicionar informações do período
            period_info = self.period_service.get_period_options().get(period, {})
            result['period_info'] = period_info
            
            return result
            
        except Exception as e:
            print(f"Erro ao obter ações com filtros: {e}")
            return {
                'stocks': [],
                'filters': {},
                'total_count': 0
            }
    
    def search_stock(self, query: str, currency: str = 'USD', language: str = 'pt-BR') -> Optional[Stock]:
        """Busca uma ação específica"""
        return self.get_stock_data(query.upper(), currency=currency, language=language)
    
    def get_market_status(self, region: str = 'US') -> Dict[str, str]:
        """Verifica status do mercado para uma região"""
        try:
            # Usar uma ação representativa para verificar o mercado
            if region == 'BR':
                test_symbol = 'VALE3.SA'
            else:
                test_symbol = 'AAPL'
            
            ticker = yf.Ticker(test_symbol)
            info = ticker.info
            
            # Yahoo Finance indica se o mercado está aberto
            market_state = info.get('marketState', 'UNKNOWN')
            
            if market_state in ['REGULAR', 'OPEN']:
                return {'status': 'open', 'message': 'Mercado Aberto'}
            elif market_state in ['CLOSED', 'POSTMARKET', 'PREMARKET']:
                return {'status': 'closed', 'message': 'Mercado Fechado'}
            else:
                return {'status': 'unknown', 'message': 'Status Desconhecido'}
                
        except Exception as e:
            print(f"Erro ao verificar status do mercado: {e}")
            return {'status': 'error', 'message': 'Erro ao verificar status'}
    
    def _map_period(self, period: str) -> str:
        """Mapeia período personalizado para formato yfinance"""
        period_map = {
            '1D': '1d',
            '5D': '5d',
            '1M': '1mo',
            '3M': '3mo',
            '6M': '6mo',
            '9M': '9mo',
            '12M': '1y'
        }
        return period_map.get(period, '1d')
    
    def get_period_options(self, language: str = 'pt-BR') -> Dict[str, str]:
        """Retorna opções de período localizadas"""
        translations = self.localization_service.translation_service
        
        periods = ['1D', '5D', '1M', '3M', '6M', '9M', '12M']
        
        return {
            period: translations.get_translation(period, language)
            for period in periods
        }
    
    def get_region_options(self, language: str = 'pt-BR') -> Dict[str, str]:
        """Retorna opções de região localizadas"""
        translations = self.localization_service.translation_service
        
        return {
            'all': translations.get_translation('all_stocks', language),
            'BR': translations.get_translation('brazilian_stocks', language),
            'US': translations.get_translation('us_stocks', language)
        }
    
    def get_trending_cryptos_with_filters(self, period: str = '1D', currency: str = 'USD', language: str = 'pt-BR', limit: int = 10) -> Dict:
        """Retorna lista de criptomoedas em alta com filtros e metadados"""
        try:
            # Para esta implementação, vamos usar os métodos existentes do tracker service
            from services.tracker_service import TrackerService
            from services.crypto_data_service import CoinGeckoProvider
            
            crypto_provider = CoinGeckoProvider()
            tracker = TrackerService(None, crypto_provider)
            
            cryptos = tracker.get_trending_cryptos(limit)
            
            # Converter preços se necessário
            if currency == 'BRL' and cryptos:
                exchange_rate = self.localization_service.get_exchange_rate('USD', 'BRL')
                for crypto in cryptos:
                    crypto.price = crypto.price * exchange_rate
                    if crypto.change_amount:
                        crypto.change_amount = crypto.change_amount * exchange_rate
            
            filters_applied = {
                'period': period,
                'currency': currency,
                'language': language
            }
            
            result = {
                'cryptos': cryptos,
                'filters': filters_applied,
                'total_count': len(cryptos)
            }
            
            # Adicionar taxa de câmbio se BRL
            if currency == 'BRL':
                result['exchange_rate'] = self.localization_service.get_exchange_rate('USD', 'BRL')
            
            return result
            
        except Exception as e:
            print(f"Erro ao obter criptos com filtros: {e}")
            return {
                'cryptos': [],
                'filters': {},
                'total_count': 0
            }
