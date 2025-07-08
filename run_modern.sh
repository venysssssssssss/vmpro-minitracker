#!/bin/bash

# Script de inicialização da aplicação moderna
# Garante que todos os componentes sejam iniciados corretamente

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    error "Python 3 não está instalado"
    exit 1
fi

# Verificar se Poetry está instalado
if ! command -v poetry &> /dev/null; then
    warn "Poetry não está instalado. Instalando..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Verificar se estamos no ambiente virtual correto
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log "Ativando ambiente virtual do Poetry..."
    poetry shell
fi

# Instalar/atualizar dependências
log "Instalando dependências..."
poetry install

# Verificar se os diretórios necessários existem
log "Verificando estrutura de diretórios..."
mkdir -p logs
mkdir -p static/css
mkdir -p static/js
mkdir -p templates/partials

# Verificar se os serviços externos estão acessíveis
log "Verificando conectividade com APIs externas..."

# Teste Yahoo Finance
if curl -s --max-time 5 "https://query1.finance.yahoo.com/v8/finance/chart/AAPL" > /dev/null; then
    log "✅ Yahoo Finance API acessível"
else
    warn "⚠️ Yahoo Finance API não acessível - usando dados de fallback"
fi

# Teste CoinGecko
if curl -s --max-time 5 "https://api.coingecko.com/api/v3/ping" > /dev/null; then
    log "✅ CoinGecko API acessível"
else
    warn "⚠️ CoinGecko API não acessível - usando dados de fallback"
fi

# Função para iniciar aplicação
start_app() {
    local app_file=${1:-"modern_fastapi_app"}
    local host=${2:-"0.0.0.0"}
    local port=${3:-"8000"}
    
    log "🚀 Iniciando VmPro Mini Tracker..."
    log "📱 Aplicação: $app_file"
    log "🌐 Host: $host"
    log "🚪 Porta: $port"
    log "📊 URL: http://$host:$port"
    log "📖 Docs: http://$host:$port/api/docs"
    
    # Verificar se a porta está disponível
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        warn "Porta $port já está em uso. Tentando parar processo existente..."
        pkill -f "uvicorn.*$app_file" || true
        sleep 2
    fi
    
    # Iniciar aplicação
    poetry run uvicorn $app_file:app \
        --host $host \
        --port $port \
        --reload \
        --log-level info \
        --access-log \
        --loop uvloop
}

# Função para parar aplicação
stop_app() {
    log "🛑 Parando aplicação..."
    pkill -f "uvicorn.*modern_fastapi_app" || true
    pkill -f "uvicorn.*fixed_fastapi_app" || true
    log "✅ Aplicação parada"
}

# Função para verificar saúde
health_check() {
    local host=${1:-"localhost"}
    local port=${2:-"8000"}
    local max_attempts=30
    local attempt=1
    
    log "🔍 Verificando saúde da aplicação..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://$host:$port/api/v3/health" > /dev/null; then
            log "✅ Aplicação está saudável!"
            curl -s "http://$host:$port/api/v3/health" | python3 -m json.tool
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    error "❌ Aplicação não respondeu dentro do tempo esperado"
    return 1
}

# Função para executar testes
run_tests() {
    log "🧪 Executando testes..."
    
    # Verificar se pytest está instalado
    if ! poetry run python -c "import pytest" 2>/dev/null; then
        warn "pytest não instalado. Instalando..."
        poetry add --group dev pytest pytest-asyncio httpx
    fi
    
    # Criar teste básico se não existir
    if [ ! -f "tests/test_basic.py" ]; then
        mkdir -p tests
        cat > tests/test_basic.py << EOF
import pytest
from fastapi.testclient import TestClient
from modern_fastapi_app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v3/health")
    assert response.status_code == 200

def test_dashboard():
    response = client.get("/")
    assert response.status_code == 200

def test_trending_stocks():
    response = client.get("/api/v3/stocks/trending?limit=5")
    assert response.status_code == 200
    
def test_trending_cryptos():
    response = client.get("/api/v3/crypto/trending?limit=5")
    assert response.status_code == 200
EOF
    fi
    
    poetry run pytest tests/ -v
}

# Função para gerar relatório de status
status_report() {
    local host=${1:-"localhost"}
    local port=${2:-"8000"}
    
    log "📊 Relatório de Status da Aplicação"
    echo "=================================="
    
    # Verificar se está rodando
    if pgrep -f "uvicorn.*modern_fastapi_app" > /dev/null; then
        log "✅ Processo da aplicação está rodando"
    else
        warn "⚠️ Processo da aplicação não está rodando"
    fi
    
    # Verificar conectividade
    if curl -s -f "http://$host:$port/api/v3/health" > /dev/null; then
        log "✅ Aplicação respondendo"
        
        # Buscar métricas
        echo ""
        log "📈 Métricas dos Serviços:"
        curl -s "http://$host:$port/api/v3/admin/metrics" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        metrics = data['data']['service_metrics']
        for service, metric in metrics.items():
            print(f'  {service}:')
            print(f'    - Requests: {metric[\"total_requests\"]}')
            print(f'    - Success Rate: {metric[\"success_rate\"]:.1f}%')
            print(f'    - Avg Response Time: {metric[\"avg_response_time\"]:.3f}s')
except:
    print('  Métricas não disponíveis')
"
    else
        error "❌ Aplicação não está respondendo"
    fi
}

# Função principal
main() {
    case ${1:-"start"} in
        "start")
            start_app "${@:2}"
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            stop_app
            sleep 2
            start_app "${@:2}"
            ;;
        "health")
            health_check "${@:2}"
            ;;
        "test")
            run_tests
            ;;
        "status")
            status_report "${@:2}"
            ;;
        "dev")
            log "🔧 Modo desenvolvimento - usando fixed_fastapi_app"
            poetry run uvicorn fixed_fastapi_app:app --host 0.0.0.0 --port 8001 --reload
            ;;
        "docker")
            log "🐳 Iniciando com Docker..."
            docker-compose up --build
            ;;
        "docker-prod")
            log "🐳 Iniciando produção com Docker..."
            docker-compose --profile production up --build -d
            ;;
        *)
            echo "Uso: $0 {start|stop|restart|health|test|status|dev|docker|docker-prod}"
            echo ""
            echo "Comandos:"
            echo "  start     - Inicia a aplicação moderna"
            echo "  stop      - Para a aplicação"
            echo "  restart   - Reinicia a aplicação"
            echo "  health    - Verifica saúde da aplicação"
            echo "  test      - Executa testes"
            echo "  status    - Mostra relatório de status"
            echo "  dev       - Inicia versão de desenvolvimento"
            echo "  docker    - Inicia com Docker Compose"
            echo "  docker-prod - Inicia produção com Docker"
            echo ""
            echo "Exemplos:"
            echo "  $0 start                    # Inicia na porta padrão 8000"
            echo "  $0 start modern_fastapi_app 0.0.0.0 8080  # Customizado"
            echo "  $0 health localhost 8000    # Verifica saúde"
            exit 1
            ;;
    esac
}

# Trap para cleanup
trap 'echo ""; log "🔄 Encerrando..."; exit 0' INT TERM

# Executar função principal
main "$@"
