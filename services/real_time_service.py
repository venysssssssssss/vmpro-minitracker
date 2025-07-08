import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List

import websockets


class RealTimeDataService:
    """Serviço para streaming de dados em tempo real"""

    def __init__(self, tracker_service):
        self.tracker_service = tracker_service
        self.subscribers = []
        self.running = False
        self.update_interval = 30  # segundos

    def subscribe(self, callback: Callable):
        """Inscrever um callback para receber atualizações"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Desinscrever um callback"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def start_streaming(self, symbols: List[str]):
        """Iniciar streaming de dados para símbolos específicos"""
        if self.running:
            return

        self.running = True
        self.symbols = symbols

        # Executar em thread separada
        thread = threading.Thread(target=self._stream_data)
        thread.daemon = True
        thread.start()

    def stop_streaming(self):
        """Parar streaming de dados"""
        self.running = False

    def _stream_data(self):
        """Loop principal do streaming"""
        while self.running:
            try:
                # Buscar dados atualizados
                updated_data = []

                # Atualizar ações
                stocks = self.tracker_service.get_multiple_stocks(
                    [s for s in self.symbols if not s.startswith('CRYPTO_')]
                )
                for stock in stocks:
                    updated_data.append(
                        {
                            'type': 'stock',
                            'data': stock.to_dict(),
                            'timestamp': datetime.now().isoformat(),
                        }
                    )

                # Atualizar criptos
                crypto_symbols = [
                    s.replace('CRYPTO_', '')
                    for s in self.symbols
                    if s.startswith('CRYPTO_')
                ]
                if crypto_symbols:
                    cryptos = self.tracker_service.get_multiple_cryptos(
                        crypto_symbols
                    )
                    for crypto in cryptos:
                        updated_data.append(
                            {
                                'type': 'crypto',
                                'data': crypto.to_dict(),
                                'timestamp': datetime.now().isoformat(),
                            }
                        )

                # Notificar subscribers
                for callback in self.subscribers:
                    try:
                        callback(updated_data)
                    except Exception as e:
                        print(f'Erro ao notificar subscriber: {e}')

                # Aguardar próxima atualização
                time.sleep(self.update_interval)

            except Exception as e:
                print(f'Erro no streaming: {e}')
                time.sleep(5)  # Aguardar antes de tentar novamente


class MarketStatusService:
    """Serviço para verificar status do mercado"""

    @staticmethod
    def is_market_open() -> bool:
        """Verifica se o mercado está aberto (simplificado)"""
        now = datetime.now()
        # Verificação simplificada - mercado americano (9:30 - 16:00 EST, seg-sex)
        weekday = now.weekday()  # 0 = segunda, 6 = domingo
        hour = now.hour

        # Mercado fechado nos fins de semana
        if weekday >= 5:  # sábado ou domingo
            return False

        # Verificar horário (aproximado, sem considerar fuso horário exato)
        if 9 <= hour <= 16:
            return True

        return False

    @staticmethod
    def get_market_status() -> Dict:
        """Retorna status detalhado do mercado"""
        is_open = MarketStatusService.is_market_open()
        now = datetime.now()

        return {
            'is_open': is_open,
            'status': 'OPEN' if is_open else 'CLOSED',
            'current_time': now.isoformat(),
            'next_open': None,  # Poderia calcular próxima abertura
            'message': 'Mercado aberto' if is_open else 'Mercado fechado',
        }


class AlertService:
    """Serviço para alertas de preços"""

    def __init__(self):
        self.alerts = []  # Lista de alertas ativos

    def add_price_alert(
        self, symbol: str, target_price: float, condition: str = 'above'
    ):
        """Adicionar alerta de preço"""
        alert = {
            'id': len(self.alerts) + 1,
            'symbol': symbol.upper(),
            'target_price': target_price,
            'condition': condition,  # 'above', 'below'
            'created_at': datetime.now(),
            'triggered': False,
        }
        self.alerts.append(alert)
        return alert['id']

    def check_alerts(self, current_data: List[Dict]):
        """Verificar alertas com dados atuais"""
        triggered_alerts = []

        for alert in self.alerts:
            if alert['triggered']:
                continue

            # Encontrar dados do símbolo
            symbol_data = None
            for data in current_data:
                if data['data']['symbol'] == alert['symbol']:
                    symbol_data = data['data']
                    break

            if not symbol_data:
                continue

            current_price = symbol_data['price']

            # Verificar condição
            if (
                alert['condition'] == 'above'
                and current_price >= alert['target_price']
            ):
                alert['triggered'] = True
                triggered_alerts.append(alert)
            elif (
                alert['condition'] == 'below'
                and current_price <= alert['target_price']
            ):
                alert['triggered'] = True
                triggered_alerts.append(alert)

        return triggered_alerts

    def get_active_alerts(self):
        """Retornar alertas ativos"""
        return [alert for alert in self.alerts if not alert['triggered']]

    def remove_alert(self, alert_id: int):
        """Remover alerta"""
        self.alerts = [
            alert for alert in self.alerts if alert['id'] != alert_id
        ]
