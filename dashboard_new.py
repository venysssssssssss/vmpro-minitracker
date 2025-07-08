# filepath: /home/synev1/dev/vmpro/app/stock-tracker/src/dashboard.py
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os
from services.tracker_service import TrackerService, PortfolioService
from services.stock_data_service import MockStockProvider, YahooFinanceProvider
from services.crypto_data_service import MockCryptoProvider, CoinGeckoProvider
from utils.config import Config

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
            'data': [stock.to_dict() for stock in stocks],
            'source': 'mock' if Config.USE_MOCK_DATA else 'real'
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
            'data': [crypto.to_dict() for crypto in cryptos],
            'source': 'mock' if Config.USE_MOCK_DATA else 'real'
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
                'data': stock.to_dict(),
                'source': 'mock' if Config.USE_MOCK_DATA else 'real'
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
                'data': crypto.to_dict(),
                'source': 'mock' if Config.USE_MOCK_DATA else 'real'
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
            'data': [stock.to_dict() for stock in stocks],
            'source': 'mock' if Config.USE_MOCK_DATA else 'real'
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
            'data': [crypto.to_dict() for crypto in cryptos],
            'source': 'mock' if Config.USE_MOCK_DATA else 'real'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def get_config():
    """API para retornar configurações do sistema"""
    return jsonify({
        'success': True,
        'data': {
            'use_mock_data': Config.USE_MOCK_DATA,
            'refresh_interval': Config.REFRESH_INTERVAL_SECONDS,
            'max_trending_items': Config.MAX_TRENDING_ITEMS,
            'version': '1.0.0'
        }
    })

if __name__ == '__main__':
    print(f"🚀 Iniciando Mini Tracker no modo {'desenvolvimento' if Config.FLASK_DEBUG else 'produção'}")
    print(f"📍 Dashboard disponível em: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
