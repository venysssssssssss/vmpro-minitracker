#!/usr/bin/env python3
"""
Mini Tracker de Ações e Criptomoedas
Aplicação principal seguindo princípios SOLID
"""

import sys
import os
from services.tracker_service import TrackerService, PortfolioService
from services.stock_data_service import MockStockProvider, YahooFinanceProvider
from services.crypto_data_service import MockCryptoProvider, CoinGeckoProvider
from utils.config import Config

def create_services():
    """Factory para criar os serviços - Princípio da Inversão de Dependência"""
    if Config.USE_MOCK_DATA:
        print("🔧 Usando dados mock para desenvolvimento")
        stock_provider = MockStockProvider()
        crypto_provider = MockCryptoProvider()
    else:
        print("🌐 Usando APIs reais")
        stock_provider = YahooFinanceProvider()
        crypto_provider = CoinGeckoProvider()
    
    tracker_service = TrackerService(stock_provider, crypto_provider)
    portfolio_service = PortfolioService(tracker_service)
    
    return tracker_service, portfolio_service

def demonstrate_functionality():
    """Demonstra as funcionalidades do tracker"""
    print("\n" + "="*60)
    print("🚀 MINI TRACKER DE AÇÕES E CRIPTOMOEDAS")
    print("="*60)
    
    tracker_service, portfolio_service = create_services()
    
    print("\n📈 AÇÕES EM ALTA:")
    print("-" * 40)
    trending_stocks = tracker_service.get_trending_stocks(5)
    for stock in trending_stocks:
        change_icon = "📈" if stock.is_gaining else "📉"
        print(f"{change_icon} {stock.symbol} ({stock.name})")
        print(f"   Preço: ${stock.price:.2f}")
        print(f"   Mudança: {stock.change_percent:.2f}% (${stock.change_amount:.2f})")
        print(f"   Market Cap: ${stock.market_cap:,.0f}" if stock.market_cap else "   Market Cap: N/A")
        print()
    
    print("\n🪙 CRIPTOMOEDAS EM ALTA:")
    print("-" * 40)
    trending_cryptos = tracker_service.get_trending_cryptos(5)
    for crypto in trending_cryptos:
        change_icon = "📈" if crypto.is_gaining else "📉"
        print(f"{change_icon} {crypto.symbol} ({crypto.name})")
        print(f"   Preço: ${crypto.price:.2f}")
        print(f"   Mudança 24h: {crypto.change_percent_24h:.2f}% (${crypto.change_amount:.2f})")
        print(f"   Market Cap: ${crypto.market_cap:,.0f}" if crypto.market_cap else "   Market Cap: N/A")
        print()
    
    # Simular um portfolio
    print("\n💼 DEMONSTRAÇÃO DE PORTFOLIO:")
    print("-" * 40)
    portfolio_service.add_stock_to_portfolio('AAPL', 10, 150.0)
    portfolio_service.add_crypto_to_portfolio('BTC', 0.1, 40000.0)
    
    summary = portfolio_service.get_portfolio_summary()
    print(f"Valor Total: ${summary['total_value']:.2f}")
    print(f"Investido: ${summary['total_invested']:.2f}")
    print(f"P&L: ${summary['total_pnl']:.2f}")
    
    print("\n" + "="*60)
    print("✅ Para usar o dashboard web, execute: python dashboard.py")
    print("🌐 Acesse: http://localhost:5000")
    print("="*60)

def run_web_dashboard():
    """Executa o dashboard web"""
    try:
        from dashboard import app
        print("\n🌐 Iniciando dashboard web...")
        print(f"📍 Acesse: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        print("❌ Pressione Ctrl+C para parar")
        
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    except ImportError as e:
        print(f"❌ Erro ao importar dashboard: {e}")
        print("📦 Instale as dependências: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Erro ao iniciar dashboard: {e}")

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'web' or sys.argv[1] == 'dashboard':
            run_web_dashboard()
        elif sys.argv[1] == 'demo':
            demonstrate_functionality()
        else:
            print("Uso: python main.py [demo|web|dashboard]")
    else:
        print("🎯 Mini Tracker de Ações e Criptomoedas")
        print("\nOpções:")
        print("  python main.py demo      - Demonstração das funcionalidades")
        print("  python main.py web       - Iniciar dashboard web")
        print("  python main.py dashboard - Iniciar dashboard web")
        print("\nPara configurar dados mock, defina: export USE_MOCK_DATA=true")

if __name__ == "__main__":
    main()