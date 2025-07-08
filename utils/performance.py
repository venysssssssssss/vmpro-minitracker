"""
Performance Monitor
Sistema de monitoramento de performance e métricas
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class PerformanceMonitor:
    """Monitor de performance para APIs e operações"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history

        # Métricas por endpoint
        self.endpoint_metrics = defaultdict(
            lambda: {
                'total_requests': 0,
                'total_time': 0.0,
                'errors': 0,
                'successes': 0,
                'avg_response_time': 0.0,
                'min_response_time': float('inf'),
                'max_response_time': 0.0,
                'recent_times': deque(
                    maxlen=100
                ),  # Últimos 100 tempos de resposta
            }
        )

        # Métricas gerais
        self.general_stats = {
            'start_time': time.time(),
            'total_requests': 0,
            'total_errors': 0,
            'uptime': 0,
        }

        # Histórico de requisições (para análise temporal)
        self.request_history = deque(maxlen=max_history)

        # Lock para thread safety
        self.lock = threading.RLock()

    def log_request(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Registra uma requisição HTTP"""
        with self.lock:
            metrics = self.endpoint_metrics[endpoint]

            # Atualizar métricas do endpoint
            metrics['total_requests'] += 1
            metrics['total_time'] += duration
            metrics['recent_times'].append(duration)

            # Atualizar min/max
            metrics['min_response_time'] = min(
                metrics['min_response_time'], duration
            )
            metrics['max_response_time'] = max(
                metrics['max_response_time'], duration
            )

            # Calcular média
            metrics['avg_response_time'] = (
                metrics['total_time'] / metrics['total_requests']
            )

            # Registrar sucesso/erro
            if 200 <= status_code < 400:
                metrics['successes'] += 1
            else:
                metrics['errors'] += 1

            # Atualizar métricas gerais
            self.general_stats['total_requests'] += 1
            if status_code >= 400:
                self.general_stats['total_errors'] += 1

            # Adicionar ao histórico
            self.request_history.append(
                {
                    'timestamp': time.time(),
                    'endpoint': endpoint,
                    'method': method,
                    'duration': duration,
                    'status_code': status_code,
                }
            )

    def log_endpoint_success(self, endpoint: str, duration: float):
        """Registra sucesso de um endpoint específico"""
        self.log_request(endpoint, 'GET', duration, 200)

    def log_endpoint_error(self, endpoint: str, error_message: str):
        """Registra erro de um endpoint específico"""
        self.log_request(endpoint, 'GET', 0.0, 500)

        # Log adicional do erro
        with self.lock:
            if 'errors_detail' not in self.endpoint_metrics[endpoint]:
                self.endpoint_metrics[endpoint]['errors_detail'] = deque(
                    maxlen=50
                )

            self.endpoint_metrics[endpoint]['errors_detail'].append(
                {'timestamp': time.time(), 'error': error_message}
            )

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas"""
        with self.lock:
            current_time = time.time()
            uptime = current_time - self.general_stats['start_time']

            # Calcular estatísticas por endpoint
            endpoint_stats = {}
            for endpoint, metrics in self.endpoint_metrics.items():
                recent_times = list(metrics['recent_times'])

                endpoint_stats[endpoint] = {
                    'total_requests': metrics['total_requests'],
                    'successes': metrics['successes'],
                    'errors': metrics['errors'],
                    'error_rate': (
                        metrics['errors'] / max(1, metrics['total_requests'])
                    )
                    * 100,
                    'avg_response_time': metrics['avg_response_time'],
                    'min_response_time': metrics['min_response_time']
                    if metrics['min_response_time'] != float('inf')
                    else 0,
                    'max_response_time': metrics['max_response_time'],
                    'recent_avg': sum(recent_times) / len(recent_times)
                    if recent_times
                    else 0,
                    'p95_response_time': self._calculate_percentile(
                        recent_times, 95
                    ),
                    'p99_response_time': self._calculate_percentile(
                        recent_times, 99
                    ),
                }

            # Calcular estatísticas de tempo
            recent_requests = [
                req
                for req in self.request_history
                if current_time - req['timestamp'] < 3600
            ]  # Última hora
            requests_per_minute = len(
                [
                    req
                    for req in recent_requests
                    if current_time - req['timestamp'] < 60
                ]
            )

            return {
                'general': {
                    'uptime_seconds': uptime,
                    'uptime_human': self._format_duration(uptime),
                    'total_requests': self.general_stats['total_requests'],
                    'total_errors': self.general_stats['total_errors'],
                    'overall_error_rate': (
                        self.general_stats['total_errors']
                        / max(1, self.general_stats['total_requests'])
                    )
                    * 100,
                    'requests_per_minute': requests_per_minute,
                    'requests_last_hour': len(recent_requests),
                },
                'endpoints': endpoint_stats,
                'system': {
                    'memory_usage': self._get_memory_usage(),
                    'request_history_size': len(self.request_history),
                },
            }

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Retorna estatísticas de um endpoint específico"""
        with self.lock:
            if endpoint not in self.endpoint_metrics:
                return {'error': 'Endpoint not found'}

            metrics = self.endpoint_metrics[endpoint]
            recent_times = list(metrics['recent_times'])

            return {
                'endpoint': endpoint,
                'total_requests': metrics['total_requests'],
                'successes': metrics['successes'],
                'errors': metrics['errors'],
                'error_rate': (
                    metrics['errors'] / max(1, metrics['total_requests'])
                )
                * 100,
                'avg_response_time': metrics['avg_response_time'],
                'min_response_time': metrics['min_response_time']
                if metrics['min_response_time'] != float('inf')
                else 0,
                'max_response_time': metrics['max_response_time'],
                'recent_avg': sum(recent_times) / len(recent_times)
                if recent_times
                else 0,
                'recent_requests': len(recent_times),
                'percentiles': {
                    'p50': self._calculate_percentile(recent_times, 50),
                    'p90': self._calculate_percentile(recent_times, 90),
                    'p95': self._calculate_percentile(recent_times, 95),
                    'p99': self._calculate_percentile(recent_times, 99),
                },
            }

    def get_slow_endpoints(
        self, threshold: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Retorna endpoints com performance ruim"""
        with self.lock:
            slow_endpoints = []

            for endpoint, metrics in self.endpoint_metrics.items():
                if (
                    metrics['avg_response_time'] > threshold
                    and metrics['total_requests'] > 5
                ):
                    slow_endpoints.append(
                        {
                            'endpoint': endpoint,
                            'avg_response_time': metrics['avg_response_time'],
                            'total_requests': metrics['total_requests'],
                            'error_rate': (
                                metrics['errors']
                                / max(1, metrics['total_requests'])
                            )
                            * 100,
                        }
                    )

            # Ordenar por tempo de resposta
            slow_endpoints.sort(
                key=lambda x: x['avg_response_time'], reverse=True
            )

            return slow_endpoints

    def get_error_summary(self) -> Dict[str, Any]:
        """Retorna resumo de erros"""
        with self.lock:
            error_summary = {
                'total_errors': self.general_stats['total_errors'],
                'endpoints_with_errors': [],
                'recent_errors': [],
            }

            # Endpoints com erros
            for endpoint, metrics in self.endpoint_metrics.items():
                if metrics['errors'] > 0:
                    error_summary['endpoints_with_errors'].append(
                        {
                            'endpoint': endpoint,
                            'error_count': metrics['errors'],
                            'error_rate': (
                                metrics['errors']
                                / max(1, metrics['total_requests'])
                            )
                            * 100,
                            'recent_errors': list(
                                metrics.get('errors_detail', [])
                            )[
                                -5:
                            ],  # Últimos 5 erros
                        }
                    )

            # Erros recentes (última hora)
            current_time = time.time()
            recent_errors = [
                req
                for req in self.request_history
                if req['status_code'] >= 400
                and current_time - req['timestamp'] < 3600
            ]

            error_summary['recent_errors'] = recent_errors[
                -10:
            ]  # Últimos 10 erros

            return error_summary

    def reset_stats(self):
        """Reseta todas as estatísticas"""
        with self.lock:
            self.endpoint_metrics.clear()
            self.request_history.clear()
            self.general_stats = {
                'start_time': time.time(),
                'total_requests': 0,
                'total_errors': 0,
                'uptime': 0,
            }

    def _calculate_percentile(
        self, values: List[float], percentile: int
    ) -> float:
        """Calcula percentil de uma lista de valores"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)

        return sorted_values[index]

    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível"""
        if seconds < 60:
            return f'{seconds:.1f}s'
        elif seconds < 3600:
            minutes = seconds / 60
            return f'{minutes:.1f}m'
        elif seconds < 86400:
            hours = seconds / 3600
            return f'{hours:.1f}h'
        else:
            days = seconds / 86400
            return f'{days:.1f}d'

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Estima uso de memória do monitor"""
        try:
            import sys

            memory_estimate = {
                'endpoint_metrics': sys.getsizeof(self.endpoint_metrics),
                'request_history': sys.getsizeof(self.request_history),
                'general_stats': sys.getsizeof(self.general_stats),
            }

            total_memory = sum(memory_estimate.values())
            memory_estimate['total_bytes'] = total_memory
            memory_estimate['total_kb'] = round(total_memory / 1024, 2)

            return memory_estimate

        except Exception:
            return {'error': 'Could not estimate memory usage'}


# ================================
# DECORATORS PARA MONITORAMENTO
# ================================


def monitor_performance(endpoint_name: str = None):
    """Decorator para monitorar performance de funções"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            name = endpoint_name or f'{func.__module__}.{func.__name__}'
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Assumindo que há uma instância global do monitor
                if hasattr(func, '_performance_monitor'):
                    func._performance_monitor.log_endpoint_success(
                        name, duration
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time

                if hasattr(func, '_performance_monitor'):
                    func._performance_monitor.log_endpoint_error(name, str(e))

                raise

        def sync_wrapper(*args, **kwargs):
            name = endpoint_name or f'{func.__module__}.{func.__name__}'
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if hasattr(func, '_performance_monitor'):
                    func._performance_monitor.log_endpoint_success(
                        name, duration
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time

                if hasattr(func, '_performance_monitor'):
                    func._performance_monitor.log_endpoint_error(name, str(e))

                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Instância global do monitor
performance_monitor = PerformanceMonitor()
