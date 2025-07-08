"""
VmPro Mini Tracker - Arquitetura Moderna v3.0.0
FastAPI Application seguindo princípios SOLID e Clean Architecture
"""
from fastapi import FastAPI, HTTPException, Query, Path, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import asyncio
from datetime import datetime
import uvicorn
import logging

# Importar Service Orchestrator (Facade Pattern)
from services.service_orchestrator import ServiceOrchestrator

# Modelos de API
from models.api_models import *

# Configuração
from utils.config import Config

# ============== LOGGING CONFIGURATION ==============

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== RESPONSE MODELS ==============

class APIResponse(BaseModel):
    success: bool
    data: Optional[Union[Dict, List]] = None
    error: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

# ============== DEPENDENCY INJECTION ==============

# Service Orchestrator Singleton
orchestrator = ServiceOrchestrator()

def get_orchestrator() -> ServiceOrchestrator:
    """Dependency provider para Service Orchestrator"""
    return orchestrator

# ============== FASTAPI APPLICATION ==============

app = FastAPI(
    title="VmPro Mini Tracker API v3.0",
    description="API moderna e escalável para rastreamento de ações e criptomoedas",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ============== MIDDLEWARES ==============

# Compressão GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configurado adequadamente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== STATIC FILES & TEMPLATES ==============

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializar Service Manager e Controllers (Dependency Injection)
service_manager = ServiceManager()

# Configurar serviços
stock_service = OptimizedStockService()
crypto_service = OptimizedCryptoService()

service_manager.set_stock_service(stock_service)
service_manager.set_crypto_service(crypto_service)

# Inicializar controllers
stock_controller = StockController(service_manager)
crypto_controller = CryptoController(service_manager)
admin_controller = AdminController(service_manager)
htmx_controller = HTMXController(service_manager, templates)

# Dependency para obter IP do cliente
def get_client_ip(request: Request) -> str:
    """Extrai IP do cliente da requisição"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ============== ROTAS DO FRONTEND ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal do dashboard"""
    return templates.TemplateResponse("dashboard_modern.html", {"request": request})

# ============== ROTAS DE AÇÕES ==============

@app.get("/api/v3/stocks/{symbol}")
async def get_stock(
    symbol: str = Path(..., description="Símbolo da ação (ex: AAPL, VALE3.SA)"),
    client_ip: str = Depends(get_client_ip)
):
    """Busca dados de uma ação específica"""
    request = StockRequest(symbol=symbol)
    return await stock_controller.get_stock(request, client_ip)

@app.get("/api/v3/stocks")
async def get_multiple_stocks(
    symbols: str = Query(..., description="Símbolos separados por vírgula"),
    client_ip: str = Depends(get_client_ip)
):
    """Busca dados de múltiplas ações"""
    request = MultipleStocksRequest(symbols=symbols)
    return await stock_controller.get_multiple_stocks(request, client_ip)

@app.get("/api/v3/stocks/trending")
async def get_trending_stocks(
    limit: int = Query(10, ge=1, le=50, description="Número de ações a retornar"),
    region: Region = Query(Region.US, description="Região do mercado (US ou BR)"),
    client_ip: str = Depends(get_client_ip)
):
    """Busca ações em alta por região"""
    request = TrendingStocksRequest(limit=limit, region=region)
    return await stock_controller.get_trending_stocks(request, client_ip)

# ============== ROTAS DE CRIPTOMOEDAS ==============

@app.get("/api/v3/crypto/{symbol}")
async def get_crypto(
    symbol: str = Path(..., description="Símbolo da criptomoeda (ex: BTC, ETH)"),
    client_ip: str = Depends(get_client_ip)
):
    """Busca dados de uma criptomoeda específica"""
    request = CryptoRequest(symbol=symbol)
    return await crypto_controller.get_crypto(request, client_ip)

@app.get("/api/v3/crypto/trending")
async def get_trending_cryptos(
    limit: int = Query(10, ge=1, le=50, description="Número de criptomoedas a retornar"),
    order_by: CryptoOrderBy = Query(CryptoOrderBy.PERCENT_CHANGE_24H, description="Ordenação"),
    client_ip: str = Depends(get_client_ip)
):
    """Busca criptomoedas em alta"""
    request = TrendingCryptosRequest(limit=limit, order_by=order_by)
    return await crypto_controller.get_trending_cryptos(request, client_ip)

# ============== ROTAS HTMX PARA FRONTEND ==============

@app.get("/htmx/stocks/trending")
async def htmx_trending_stocks(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    region: str = Query("US")
):
    """Endpoint HTMX para ações em alta"""
    return await htmx_controller.htmx_trending_stocks(request, limit, region)

@app.get("/htmx/crypto/trending")
async def htmx_trending_cryptos(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    order_by: str = Query("percent_change_24h")
):
    """Endpoint HTMX para criptomoedas em alta"""
    return await htmx_controller.htmx_trending_cryptos(request, limit, order_by)

# ============== ROTAS ADMINISTRATIVAS ==============

@app.get("/api/v3/health")
async def health_check():
    """Health check completo da API"""
    return await admin_controller.health_check()

@app.post("/api/v3/admin/cache/clear")
async def clear_cache(client_ip: str = Depends(get_client_ip)):
    """Limpa todos os caches"""
    return await admin_controller.clear_cache(client_ip)

@app.get("/api/v3/admin/cache/stats")
async def get_cache_stats(client_ip: str = Depends(get_client_ip)):
    """Retorna estatísticas dos caches e serviços"""
    return await admin_controller.get_cache_stats(client_ip)

@app.get("/api/v3/admin/metrics")
async def get_service_metrics():
    """Retorna métricas detalhadas dos serviços"""
    try:
        metrics = {
            "service_metrics": service_manager.get_service_metrics(),
            "circuit_breakers": service_manager.get_circuit_breaker_status(),
            "timestamp": datetime.now().isoformat()
        }
        
        return service_manager.response_formatter.format_success_response(metrics)
        
    except Exception as e:
        return service_manager.response_formatter.format_error_response(
            f"Erro ao obter métricas: {str(e)}",
            500
        )

# ============== ROTAS LEGADAS PARA COMPATIBILIDADE ==============

@app.get("/api/v2/stocks/{symbol}")
async def get_stock_v2(symbol: str, client_ip: str = Depends(get_client_ip)):
    """Compatibilidade com versão anterior"""
    return await get_stock(symbol, client_ip)

@app.get("/api/v2/stocks")
async def get_multiple_stocks_v2(symbols: str, client_ip: str = Depends(get_client_ip)):
    """Compatibilidade com versão anterior"""
    return await get_multiple_stocks(symbols, client_ip)

@app.get("/api/v2/stocks/trending")
async def get_trending_stocks_v2(
    limit: int = 10,
    region: str = "US",
    client_ip: str = Depends(get_client_ip)
):
    """Compatibilidade com versão anterior"""
    region_enum = Region.US if region.upper() == "US" else Region.BR
    return await get_trending_stocks(limit, region_enum, client_ip)

@app.get("/api/v2/crypto/{symbol}")
async def get_crypto_v2(symbol: str, client_ip: str = Depends(get_client_ip)):
    """Compatibilidade com versão anterior"""
    return await get_crypto(symbol, client_ip)

@app.get("/api/v2/crypto/trending")
async def get_trending_cryptos_v2(
    limit: int = 10,
    order_by: str = "percent_change_24h",
    client_ip: str = Depends(get_client_ip)
):
    """Compatibilidade com versão anterior"""
    order_by_enum = CryptoOrderBy.PERCENT_CHANGE_24H
    if order_by == "market_cap":
        order_by_enum = CryptoOrderBy.MARKET_CAP
    elif order_by == "volume":
        order_by_enum = CryptoOrderBy.VOLUME
    elif order_by == "price":
        order_by_enum = CryptoOrderBy.PRICE
    
    return await get_trending_cryptos(limit, order_by_enum, client_ip)

# Rota v2 para cache
@app.post("/api/v2/admin/cache/clear")
async def clear_cache_v2(client_ip: str = Depends(get_client_ip)):
    """Compatibilidade com versão anterior"""
    return await clear_cache(client_ip)

# ============== EVENTOS DO CICLO DE VIDA ==============

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    print("🚀 Iniciando VmPro Mini Tracker v3.0.0")
    print("📊 Arquitetura moderna com princípios SOLID ativada")
    
    # Verificar saúde inicial dos serviços
    health = await service_manager.health_check()
    print(f"📈 Serviços iniciados: {health['summary']['healthy_services']}/{health['summary']['total_services']}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    print("🔄 Encerrando aplicação...")
    
    # Limpar recursos se necessário
    try:
        await service_manager.clear_all_caches()
        print("🧹 Caches limpos")
    except Exception as e:
        print(f"⚠️ Erro ao limpar caches: {e}")

# ============== EXECUTAR APLICAÇÃO ==============

if __name__ == "__main__":
    uvicorn.run(
        "modern_fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
