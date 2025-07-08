# VmPro Mini Tracker v3.0.0

## 🚀 Arquitetura Moderna com Princípios SOLID

Uma aplicação web moderna para rastreamento de ações e criptomoedas em tempo real, construída com FastAPI seguindo os princípios SOLID e padrões de design avançados.

### ✨ Características Principais

- 🏗️ **Arquitetura SOLID**: Implementação completa dos princípios SOLID
- 🔄 **Circuit Breaker Pattern**: Proteção contra falhas em cascata
- 📊 **Rate Limiting**: Controle inteligente de taxa de requisições
- 🎯 **Dependency Injection**: Inversão de controle e baixo acoplamento
- 📈 **Fallback Data**: Dados de exemplo quando APIs externas falham
- 🔍 **Health Checks**: Monitoramento completo da saúde dos serviços
- ⚡ **Performance Otimizada**: Cache inteligente e processamento assíncrono
- 🐳 **Docker Ready**: Containerização completa com multi-stage build

### 🏛️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                     Controllers Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │   Stock     │ │   Crypto    │ │    Admin    │ │  HTMX  │ │
│  │ Controller  │ │ Controller  │ │ Controller  │ │ Ctrl   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Service Manager                           │
│         ┌─────────────────────────────────────────┐         │
│         │        Circuit Breaker Pattern          │         │
│         │        Rate Limiting                    │         │
│         │        Health Monitoring                │         │
│         └─────────────────────────────────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                   Services Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Stock     │ │   Crypto    │ │  Fallback   │           │
│  │  Service    │ │  Service    │ │   Service   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│                   External APIs                             │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │   Yahoo     │ │  CoinGecko  │                           │
│  │  Finance    │ │     API     │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 Princípios SOLID Implementados

#### 1. **S**ingle Responsibility Principle
- Cada classe tem uma única responsabilidade
- `StockController` apenas para lógica de ações
- `CryptoController` apenas para lógica de criptomoedas
- `ServiceManager` apenas para gerenciamento de serviços

#### 2. **O**pen/Closed Principle
- Interfaces permitem extensão sem modificação
- Novos serviços podem ser adicionados implementando `IDataService`
- Estratégias de cache podem ser trocadas via interface

#### 3. **L**iskov Substitution Principle
- Implementações podem ser substituídas por suas interfaces
- `OptimizedStockService` pode ser substituído por qualquer `IStockService`

#### 4. **I**nterface Segregation Principle
- Interfaces específicas e focadas
- `IStockService`, `ICryptoService`, `ICacheManager` são independentes

#### 5. **D**ependency Inversion Principle
- Dependência de abstrações, não implementações
- `ServiceManager` usa interfaces, não classes concretas
- Injeção de dependência via setters

### 🚀 Quick Start

#### Método 1: Script Automatizado (Recomendado)
```bash
# Iniciar aplicação moderna
./run_modern.sh start

# Verificar saúde
./run_modern.sh health

# Ver status completo
./run_modern.sh status

# Parar aplicação
./run_modern.sh stop
```

#### Método 2: Manual
```bash
# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell

# Iniciar aplicação
uvicorn modern_fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

#### Método 3: Docker
```bash
# Desenvolvimento
./run_modern.sh docker

# Produção
./run_modern.sh docker-prod
```

### 📡 Endpoints da API

#### V3 (Nova Arquitetura)
- `GET /api/v3/stocks/{symbol}` - Dados de uma ação
- `GET /api/v3/stocks/trending` - Ações em alta
- `GET /api/v3/crypto/{symbol}` - Dados de uma criptomoeda
- `GET /api/v3/crypto/trending` - Criptomoedas em alta
- `GET /api/v3/health` - Health check completo
- `GET /api/v3/admin/metrics` - Métricas dos serviços
- `POST /api/v3/admin/cache/clear` - Limpar cache

#### V2 (Compatibilidade)
- Mantém compatibilidade com versão anterior
- Redirecionamento automático para V3

#### HTMX (Frontend)
- `GET /htmx/stocks/trending` - Tabela de ações
- `GET /htmx/crypto/trending` - Tabela de criptomoedas

### 🔍 Monitoramento e Métricas

#### Health Check
```bash
curl http://localhost:8000/api/v3/health
```

Retorna:
```json
{
  "success": true,
  "data": {
    "services": {
      "stock_service": {
        "status": "available",
        "healthy": true
      },
      "crypto_service": {
        "status": "available", 
        "healthy": true
      }
    },
    "summary": {
      "total_services": 2,
      "healthy_services": 2,
      "overall_healthy": true
    }
  }
}
```

#### Métricas dos Serviços
```bash
curl http://localhost:8000/api/v3/admin/metrics
```

### 🛡️ Rate Limiting e Circuit Breaker

#### Rate Limiting
- 60 requisições por minuto por IP para endpoints normais
- 10 requisições por minuto para endpoints administrativos
- Headers de rate limit incluídos nas respostas

#### Circuit Breaker
- Threshold: 5 falhas consecutivas
- Timeout: 60 segundos
- Estados: Closed → Open → Half-Open → Closed

### 🎯 Fallback e Resiliência

Quando APIs externas falham:
1. **Cache**: Retorna dados em cache se disponíveis
2. **Fallback**: Usa dados de exemplo realistas
3. **Circuit Breaker**: Evita sobrecarga de APIs com problemas
4. **Indicadores**: Frontend mostra quando dados são de fallback

### 🧪 Testes

```bash
# Executar todos os testes
./run_modern.sh test

# Ou manualmente
poetry run pytest tests/ -v
```

### 🐳 Docker e Produção

#### Desenvolvimento
```bash
docker-compose up --build
```

#### Produção
```bash
docker-compose --profile production up -d
```

Inclui:
- Aplicação principal
- Redis para cache
- Nginx para reverse proxy
- Prometheus para métricas
- Grafana para visualização

### 📊 Estrutura do Projeto

```
vmpro-minitracker/
├── controllers/           # Controladores (MVC)
│   └── modern_controllers.py
├── interfaces/           # Interfaces e contratos
│   ├── service_interfaces.py
│   └── data_provider.py
├── services/            # Serviços de negócio
│   ├── service_manager.py
│   ├── optimized_stock_service.py
│   ├── optimized_crypto_service.py
│   └── fallback_data_service.py
├── templates/           # Templates Jinja2
│   ├── dashboard_modern.html
│   └── partials/
├── static/             # Arquivos estáticos
├── tests/              # Testes automatizados
├── modern_fastapi_app.py    # Aplicação principal V3
├── fixed_fastapi_app.py     # Aplicação V2 (compatibilidade)
├── Dockerfile          # Container da aplicação
├── docker-compose.yml  # Orquestração
├── run_modern.sh      # Script de inicialização
└── README.md          # Esta documentação
```

### 🔧 Configuração

#### Variáveis de Ambiente
```bash
# APIs
USE_MOCK_DATA=false

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=true

# Performance
CACHE_TTL_STOCKS=900     # 15 minutos
CACHE_TTL_CRYPTO=180     # 3 minutos
MAX_CONCURRENT_REQUESTS=10

# Rate Limiting
REQUESTS_PER_MINUTE=60
```

### 🚨 Troubleshooting

#### APIs Externas com Rate Limit
```bash
# Limpar cache para forçar novos dados
curl -X POST http://localhost:8000/api/v3/admin/cache/clear

# Verificar status dos serviços
curl http://localhost:8000/api/v3/health
```

#### Aplicação Não Responde
```bash
# Verificar processo
./run_modern.sh status

# Reiniciar
./run_modern.sh restart

# Ver logs
docker-compose logs vmpro-tracker
```

### 📈 Performance

#### Otimizações Implementadas
- **Cache Inteligente**: TTL diferenciado por tipo de dados
- **Processamento Assíncrono**: ThreadPoolExecutor para I/O
- **Rate Limiting**: Evita sobrecarga de APIs
- **Batch Processing**: Requisições em lotes para reduzir latência
- **Fallback Rápido**: Dados de exemplo quando APIs falham

#### Benchmarks
- Response time médio: < 100ms para dados em cache
- Response time médio: < 500ms para dados novos
- Throughput: > 1000 req/s em hardware modesto

### 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### 📝 Changelog

#### v3.0.0 (Atual)
- ✨ Arquitetura SOLID completa
- ✨ Circuit Breaker Pattern
- ✨ Rate Limiting avançado
- ✨ Dependency Injection
- ✨ Health Monitoring
- ✨ Docker Support
- ✨ Fallback Data Service

#### v2.0.0
- Implementação FastAPI básica
- Cache simples
- APIs de ações e criptomoedas

#### v1.0.0
- Versão inicial Flask

### 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.

### 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/vmpro-minitracker/issues)
- **Documentação**: [API Docs](http://localhost:8000/api/docs)
- **Email**: seu-email@exemplo.com

---

🎯 **VmPro Mini Tracker** - Rastreamento financeiro moderno e resiliente!
