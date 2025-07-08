from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os
from services.tracker_service import TrackerService, PortfolioService
from services.stock_data_service import MockStockProvider, YahooFinanceProvider
from services.crypto_data_service import MockCryptoProvider, CoinGeckoProvider
from services.integrated_data_service import IntegratedStockService
from services.localization_service import LocalizationService
from utils.config import Config
# Importar serviços de tempo real
from services.real_time_service import MarketStatusService, AlertService

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# Inicializar serviços baseado na configuração
print(f"🔧 Configuração: {'Dados Mock' if Config.USE_MOCK_DATA else 'APIs Reais'}")

if Config.USE_MOCK_DATA:
    stock_provider = MockStockProvider()
    crypto_provider = MockCryptoProvider()
    print("📊 Usando dados mock para desenvolvimento")
else:
    stock_provider = YahooFinanceProvider()
    crypto_provider = CoinGeckoProvider()
    print("🌐 Usando APIs reais (Yahoo Finance + CoinGecko)")

tracker_service = TrackerService(stock_provider, crypto_provider)
portfolio_service = PortfolioService(tracker_service)
# Novos serviços integrados
integrated_stock_service = IntegratedStockService()
localization_service = LocalizationService()
# Inicializar serviços adicionais
alert_service = AlertService()

@app.route('/')
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/trending/stocks')
def get_trending_stocks():
    """API para buscar ações em alta"""
    try:
        limit = request.args.get('limit', Config.MAX_TRENDING_ITEMS, type=int)
        stocks = tracker_service.get_trending_stocks(limit)
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in stocks]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/v2/trending/stocks')
def get_trending_stocks_v2():
    """API v2 para buscar ações em alta com filtros"""
    try:
        region = request.args.get('region', 'all')  # all, BR, US
        period = request.args.get('period', '1D')   # 1D, 5D, 1M, 3M, 6M, 9M, 12M
        currency = request.args.get('currency', 'USD')  # USD, BRL
        language = request.args.get('lang', 'pt-BR')    # pt-BR, en-US
        limit = request.args.get('limit', 10, type=int)
        
        stocks = integrated_stock_service.get_trending_stocks(
            region=region, 
            period=period, 
            currency=currency, 
            language=language, 
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in stocks],
            'filters': {
                'region': region,
                'period': period,
                'currency': currency,
                'language': language
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trending/cryptos')
def get_trending_cryptos():
    """API para buscar criptomoedas em alta"""
    try:
        limit = request.args.get('limit', Config.MAX_TRENDING_ITEMS, type=int)
        cryptos = tracker_service.get_trending_cryptos(limit)
        return jsonify({
            'success': True,
            'data': [crypto.to_dict() for crypto in cryptos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    """API para buscar dados de uma ação específica"""
    try:
        stock = tracker_service.get_stock_data(symbol)
        if stock:
            return jsonify({
                'success': True,
                'data': stock.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Stock not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crypto/<symbol>')
def get_crypto(symbol):
    """API para buscar dados de uma criptomoeda específica"""
    try:
        crypto = tracker_service.get_crypto_data(symbol)
        if crypto:
            return jsonify({
                'success': True,
                'data': crypto.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Crypto not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """API para buscar resumo do portfolio"""
    try:
        summary = portfolio_service.get_portfolio_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/stock', methods=['POST'])
def add_stock_to_portfolio():
    """API para adicionar ação ao portfolio"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        purchase_price = data.get('purchase_price')
        
        if not all([symbol, quantity, purchase_price]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, quantity, purchase_price'
            }), 400
        
        portfolio_service.add_stock_to_portfolio(symbol, quantity, purchase_price)
        return jsonify({
            'success': True,
            'message': f'Stock {symbol} added to portfolio'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/crypto', methods=['POST'])
def add_crypto_to_portfolio():
    """API para adicionar criptomoeda ao portfolio"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        purchase_price = data.get('purchase_price')
        
        if not all([symbol, quantity, purchase_price]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, quantity, purchase_price'
            }), 400
        
        portfolio_service.add_crypto_to_portfolio(symbol, quantity, purchase_price)
        return jsonify({
            'success': True,
            'message': f'Crypto {symbol} added to portfolio'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/stocks')
def search_stocks():
    """API para buscar múltiplas ações"""
    try:
        symbols_param = request.args.get('symbols', '')
        if not symbols_param:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        symbols = [s.strip().upper() for s in symbols_param.split(',')]
        stocks = tracker_service.get_multiple_stocks(symbols)
        
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in stocks]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/cryptos')
def search_cryptos():
    """API para buscar múltiplas criptomoedas"""
    try:
        symbols_param = request.args.get('symbols', '')
        if not symbols_param:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        symbols = [s.strip().upper() for s in symbols_param.split(',')]
        cryptos = tracker_service.get_multiple_cryptos(symbols)
        
        return jsonify({
            'success': True,
            'data': [crypto.to_dict() for crypto in cryptos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market/status')
def get_market_status():
    """API para verificar status do mercado"""
    try:
        status = MarketStatusService.get_market_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """API para listar alertas ativos"""
    try:
        alerts = alert_service.get_active_alerts()
        return jsonify({
            'success': True,
            'data': alerts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """API para criar alerta de preço"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        target_price = data.get('target_price')
        condition = data.get('condition', 'above')
        
        if not all([symbol, target_price]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, target_price'
            }), 400
        
        alert_id = alert_service.add_price_alert(symbol, float(target_price), condition)
        return jsonify({
            'success': True,
            'data': {'alert_id': alert_id},
            'message': f'Alert created for {symbol} at ${target_price}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """API para deletar alerta"""
    try:
        alert_service.remove_alert(alert_id)
        return jsonify({
            'success': True,
            'message': 'Alert deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch/stocks')
def get_batch_stocks():
    """API para buscar múltiplas ações em uma requisição"""
    try:
        symbols = Config.DEFAULT_STOCKS
        custom_symbols = request.args.get('symbols')
        if custom_symbols:
            symbols = [s.strip().upper() for s in custom_symbols.split(',')]
        
        stocks = tracker_service.get_multiple_stocks(symbols)
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in stocks],
            'count': len(stocks),
            'requested_symbols': symbols
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch/cryptos')
def get_batch_cryptos():
    """API para buscar múltiplas criptomoedas em uma requisição"""
    try:
        symbols = Config.DEFAULT_CRYPTOS
        custom_symbols = request.args.get('symbols')
        if custom_symbols:
            symbols = [s.strip().upper() for s in custom_symbols.split(',')]
        
        cryptos = tracker_service.get_multiple_cryptos(symbols)
        return jsonify({
            'success': True,
            'data': [crypto.to_dict() for crypto in cryptos],
            'count': len(cryptos),
            'requested_symbols': symbols
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def get_config():
    """API para obter configurações do sistema"""
    from utils.config import get_config
    try:
        config_data = get_config()
        return jsonify({
            'success': True,
            'data': config_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/currencies')
def get_currencies():
    """API para obter moedas disponíveis"""
    try:
        currencies = localization_service.get_available_currencies()
        return jsonify({
            'success': True,
            'data': currencies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/languages')
def get_languages():
    """API para obter idiomas disponíveis"""
    try:
        languages = localization_service.get_available_languages()
        return jsonify({
            'success': True,
            'data': languages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/regions')
def get_regions():
    """API para obter regiões disponíveis"""
    try:
        regions = localization_service.get_available_regions()
        return jsonify({
            'success': True,
            'data': regions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/periods')
def get_periods():
    """API para obter períodos disponíveis"""
    try:
        periods = localization_service.get_available_periods()
        return jsonify({
            'success': True,
            'data': periods
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/translate')
def translate_text():
    """API para traduzir texto"""
    try:
        text = request.args.get('text', '')
        language = request.args.get('language', 'pt-BR')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text parameter is required'
            }), 400
            
        translated = localization_service.translate(text, language)
        return jsonify({
            'success': True,
            'data': {
                'original': text,
                'translated': translated,
                'language': language
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localization/convert')
def convert_currency():
    """API para conversão de moeda"""
    try:
        amount = request.args.get('amount', type=float)
        from_currency = request.args.get('from', 'USD')
        to_currency = request.args.get('to', 'BRL')
        
        if amount is None:
            return jsonify({
                'success': False,
                'error': 'Amount parameter is required'
            }), 400
            
        converted = localization_service.convert_currency(amount, from_currency, to_currency)
        exchange_rate = localization_service.get_exchange_rate(from_currency, to_currency)
        
        return jsonify({
            'success': True,
            'data': {
                'original_amount': amount,
                'converted_amount': converted,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v3/trending/stocks')
def get_trending_stocks_v3():
    """API v3 para buscar ações em alta com todos os filtros integrados"""
    try:
        # Parâmetros de filtro
        region = request.args.get('region', 'all')
        period = request.args.get('period', '1D')
        currency = request.args.get('currency', 'USD')
        language = request.args.get('language', 'pt-BR')
        limit = request.args.get('limit', 10, type=int)
        
        # Usar o serviço integrado
        result = integrated_stock_service.get_trending_stocks_with_filters(
            region=region,
            period=period,
            currency=currency,
            language=language,
            limit=limit
        )
        
        # Converter Stock objects para dicionários
        stock_data = []
        for stock in result['stocks']:
            stock_dict = stock.to_dict() if hasattr(stock, 'to_dict') else {
                'symbol': stock.symbol,
                'name': stock.name,
                'price': stock.price,
                'previous_close': stock.previous_close,
                'change_percent': stock.change_percent,
                'market_cap': stock.market_cap,
                'volume': stock.volume,
                'last_updated': str(stock.last_updated)
            }
            # Adicionar preço formatado
            if currency:
                stock_dict['formatted_price'] = localization_service.format_currency(stock.price, currency)
            stock_data.append(stock_dict)
        
        return jsonify({
            'success': True,
            'data': stock_data,
            'metadata': {
                'filters_applied': result['filters'],
                'total_count': len(result['stocks']),
                'exchange_rate': result.get('exchange_rate'),
                'language': language,
                'period_info': result.get('period_info')
            }
        })
    except Exception as e:
        print(f"Erro na API v3 stocks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v3/trending/cryptos')
def get_trending_cryptos_v3():
    """API v3 para buscar criptomoedas em alta com filtros"""
    try:
        period = request.args.get('period', '1D')
        currency = request.args.get('currency', 'USD')
        language = request.args.get('language', 'pt-BR')
        limit = request.args.get('limit', 10, type=int)
        
        result = integrated_stock_service.get_trending_cryptos_with_filters(
            period=period,
            currency=currency,
            language=language,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': result['cryptos'],
            'metadata': {
                'filters_applied': result['filters'],
                'total_count': len(result['cryptos']),
                'exchange_rate': result.get('exchange_rate'),
                'language': language
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
