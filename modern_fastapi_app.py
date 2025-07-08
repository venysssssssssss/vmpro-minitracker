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

# ============== EVENT HANDLERS ==============

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    logger.info("🚀 Iniciando VmPro Mini Tracker v3.0.0")
    logger.info("📊 Arquitetura moderna com princípios SOLID ativada")
    
    # Inicializar orchestrator
    try:
        await orchestrator.initialize()
        logger.info("📈 Serviços iniciados: 2/2")
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza na finalização da aplicação"""
    logger.info("🔴 Encerrando VmPro Mini Tracker v3.0.0")

# ============== FRONTEND ROUTES ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal do dashboard moderno"""
    return templates.TemplateResponse("dashboard_modern.html", {"request": request})

# ============== API ROUTES - STOCKS ==============

@app.get("/api/v3/stocks/{symbol}", response_model=APIResponse)
async def get_stock(
    symbol: str = Path(..., description="Símbolo da ação"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Busca dados de uma ação específica"""
    try:
        data = await orchestrator.get_stock_data(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Ação {symbol} não encontrada")
        
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar ação {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v3/stocks/trending", response_model=APIResponse)
async def get_trending_stocks(
    limit: int = Query(10, ge=1, le=50, description="Número de ações"),
    region: str = Query("US", description="Região do mercado (US ou BR)"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Busca ações em alta por região"""
    try:
        data = await orchestrator.get_trending_stocks(limit=limit, region=region.upper())
        return APIResponse(success=True, data=data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar trending stocks: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# ============== API ROUTES - CRYPTO ==============

@app.get("/api/v3/crypto/{symbol}", response_model=APIResponse)
async def get_crypto(
    symbol: str = Path(..., description="Símbolo da criptomoeda"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Busca dados de uma criptomoeda específica"""
    try:
        data = await orchestrator.get_crypto_data(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Criptomoeda {symbol} não encontrada")
        
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar crypto {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/v3/crypto/trending", response_model=APIResponse)
async def get_trending_cryptos(
    limit: int = Query(10, ge=1, le=50, description="Número de criptomoedas"),
    order_by: str = Query("percent_change_24h", description="Ordenação"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Busca criptomoedas em alta"""
    try:
        valid_orders = ["percent_change_24h", "market_cap", "volume", "price"]
        if order_by not in valid_orders:
            raise HTTPException(status_code=400, detail=f"order_by deve ser um de: {valid_orders}")
        
        data = await orchestrator.get_trending_cryptos(limit=limit, order_by=order_by)
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar trending cryptos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# ============== HTMX ROUTES FOR FRONTEND ==============

@app.get("/htmx/stocks/trending")
async def htmx_trending_stocks(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    region: str = Query("US"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Endpoint HTMX para ações em alta"""
    try:
        stocks = await orchestrator.get_trending_stocks(limit=limit, region=region.upper())
        
        return templates.TemplateResponse(
            "partials/new_stocks_table.html",
            {"request": request, "stocks": stocks, "region": region.upper()}
        )
        
    except Exception as e:
        logger.error(f"Erro HTMX stocks: {e}")
        return f"<div class='error'>Erro ao carregar ações: {str(e)}</div>"

@app.get("/htmx/crypto/trending")
async def htmx_trending_cryptos(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    order_by: str = Query("percent_change_24h"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Endpoint HTMX para criptomoedas em alta"""
    try:
        cryptos = await orchestrator.get_trending_cryptos(limit=limit, order_by=order_by)
        
        return templates.TemplateResponse(
            "partials/crypto_table.html",
            {"request": request, "cryptos": cryptos, "order_by": order_by}
        )
        
    except Exception as e:
        logger.error(f"Erro HTMX crypto: {e}")
        return f"<div class='error'>Erro ao carregar criptomoedas: {str(e)}</div>"

# ============== ADMIN ROUTES ==============

@app.post("/api/v3/admin/cache/clear", response_model=APIResponse)
async def clear_cache(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Limpa o cache dos serviços"""
    try:
        result = await orchestrator.clear_all_caches()
        return APIResponse(success=result['success'], data=result)
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro ao limpar cache")

@app.get("/api/v3/admin/metrics", response_model=APIResponse)
async def get_metrics(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Retorna métricas do sistema"""
    try:
        metrics = await orchestrator.get_system_metrics()
        return APIResponse(success=True, data=metrics)
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter métricas")

# ============== HEALTH & MONITORING ==============

@app.get("/api/v3/health", response_model=APIResponse)
async def health_check(
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Health check da API"""
    try:
        health_data = await orchestrator.health_check()
        return APIResponse(success=True, data=health_data)
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail="Erro no health check")

# ============== LEGACY COMPATIBILITY ROUTES ==============

# V2 Compatibility
@app.post("/api/v2/admin/cache/clear", response_model=APIResponse)
async def clear_cache_v2(orchestrator: ServiceOrchestrator = Depends(get_orchestrator)):
    """Compatibilidade com v2"""
    return await clear_cache(orchestrator)

@app.get("/api/v2/stocks/trending", response_model=APIResponse)
async def get_trending_stocks_v2(
    limit: int = Query(10, ge=1, le=50),
    region: str = Query("US"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Compatibilidade com v2"""
    return await get_trending_stocks(limit, region, orchestrator)

@app.get("/api/v2/crypto/trending", response_model=APIResponse)
async def get_trending_cryptos_v2(
    limit: int = Query(10, ge=1, le=50),
    order_by: str = Query("percent_change_24h"),
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator)
):
    """Compatibilidade com v2"""
    return await get_trending_cryptos(limit, order_by, orchestrator)

# ============== EXCEPTION HANDLERS ==============

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handler para 404"""
    return APIResponse(success=False, error="Endpoint não encontrado")

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handler para 500"""
    return APIResponse(success=False, error="Erro interno do servidor")

# ============== APPLICATION RUNNER ==============

if __name__ == "__main__":
    uvicorn.run(
        "modern_fastapi_app:app",
        host=Config.FASTAPI_HOST,
        port=Config.FASTAPI_PORT,
        reload=Config.FASTAPI_RELOAD,
        log_level="info"
    )
