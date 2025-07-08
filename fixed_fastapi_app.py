"""
FastAPI Application para Mini Tracker de Ações e Criptomoedas
API moderna e otimizada com documentação automática
"""
from fastapi import FastAPI, HTTPException, Query, Path, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import asyncio
from datetime import datetime
import uvicorn

# Importar serviços otimizados
from services.optimized_stock_service import OptimizedStockService
from services.optimized_crypto_service import OptimizedCryptoService

# Modelos Pydantic para validação
class APIResponse(BaseModel):
    success: bool
    data: Optional[Union[Dict, List]] = None
    error: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

# Criar aplicação FastAPI
app = FastAPI(
    title="VmPro Mini Tracker API",
    description="API moderna para rastreamento de ações e criptomoedas em tempo real",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializar serviços
stock_service = OptimizedStockService()
crypto_service = OptimizedCryptoService()

# ============== ROTAS DO FRONTEND ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal do dashboard"""
    return templates.TemplateResponse("dashboard_modern.html", {"request": request})

# ============== ROTAS DE AÇÕES ==============

@app.get("/api/v2/stocks/{symbol}", response_model=APIResponse)
async def get_stock(symbol: str = Path(..., description="Símbolo da ação (ex: AAPL, VALE3.SA)")):
    """Busca dados de uma ação específica"""
    try:
        data = await stock_service.get_stock_data(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Ação {symbol} não encontrada")
        
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v2/stocks", response_model=APIResponse)
async def get_multiple_stocks(symbols: str = Query(..., description="Símbolos separados por vírgula")):
    """Busca dados de múltiplas ações"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Máximo de 20 símbolos por vez")
        
        data = await stock_service.get_multiple_stocks(symbol_list)
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v2/stocks/trending", response_model=APIResponse)
async def get_trending_stocks(
    limit: int = Query(10, ge=1, le=50, description="Número de ações a retornar"),
    region: str = Query("US", description="Região do mercado (US ou BR)")
):
    """Busca ações em alta por região"""
    try:
        data = await stock_service.get_trending_stocks(limit=limit, region=region.upper())
        return APIResponse(success=True, data=data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ============== ROTAS DE CRIPTOMOEDAS ==============

@app.get("/api/v2/crypto/{symbol}", response_model=APIResponse)
async def get_crypto(symbol: str = Path(..., description="Símbolo da criptomoeda (ex: BTC, ETH)")):
    """Busca dados de uma criptomoeda específica"""
    try:
        data = await crypto_service.get_crypto_data(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Criptomoeda {symbol} não encontrada")
        
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v2/crypto/trending", response_model=APIResponse)
async def get_trending_cryptos(
    limit: int = Query(10, ge=1, le=50, description="Número de criptomoedas a retornar"),
    order_by: str = Query("percent_change_24h", description="Ordenação")
):
    """Busca criptomoedas em alta"""
    try:
        valid_orders = ["percent_change_24h", "market_cap", "volume", "price"]
        if order_by not in valid_orders:
            raise HTTPException(status_code=400, detail=f"order_by deve ser um de: {valid_orders}")
        
        data = await crypto_service.get_trending_cryptos(limit=limit, order_by=order_by)
        return APIResponse(success=True, data=data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ============== ROTAS HTMX PARA FRONTEND ==============

@app.get("/htmx/stocks/trending")
async def htmx_trending_stocks(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    region: str = Query("US")
):
    """Endpoint HTMX para ações em alta"""
    try:
        stocks = await stock_service.get_trending_stocks(limit=limit, region=region.upper())
        
        return templates.TemplateResponse(
            "partials/new_stocks_table.html",
            {"request": request, "stocks": stocks, "region": region.upper()}
        )
        
    except Exception as e:
        return f"<div class='error'>Erro ao carregar ações: {str(e)}</div>"

@app.get("/htmx/crypto/trending")
async def htmx_trending_cryptos(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    order_by: str = Query("percent_change_24h")
):
    """Endpoint HTMX para criptomoedas em alta"""
    try:
        cryptos = await crypto_service.get_trending_cryptos(limit=limit, order_by=order_by)
        
        return templates.TemplateResponse(
            "partials/crypto_table.html",
            {"request": request, "cryptos": cryptos, "order_by": order_by}
        )
        
    except Exception as e:
        return f"<div class='error'>Erro ao carregar criptomoedas: {str(e)}</div>"

@app.get("/api/v2/health", response_model=APIResponse)
async def health_check():
    """Health check da API"""
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.post("/api/v2/admin/cache/clear", response_model=APIResponse)
async def clear_cache():
    """Limpa o cache dos serviços"""
    try:
        stock_service.clear_cache()
        crypto_service.clear_cache()
        
        return APIResponse(
            success=True,
            data={"message": "Cache limpo com sucesso"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")

@app.get("/api/v2/admin/cache/stats", response_model=APIResponse)
async def get_cache_stats():
    """Retorna estatísticas do cache"""
    try:
        stock_stats = stock_service.get_cache_stats()
        crypto_stats = crypto_service.get_cache_stats()
        
        return APIResponse(
            success=True,
            data={
                "stock_cache": stock_stats,
                "crypto_cache": crypto_stats
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

# ============== EXECUTAR APLICAÇÃO ==============

if __name__ == "__main__":
    uvicorn.run(
        "new_fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
