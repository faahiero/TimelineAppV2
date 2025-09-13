"""
Sistema de rate limiting para respeitar limites de APIs
"""
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional
import requests
from functools import wraps

class RateLimiter:
    """Rate limiter thread-safe para controlar requisições"""
    
    def __init__(self):
        self.limits = {
            'wikipedia': {'requests': 100, 'window': 60},  # 100 req/min
            'wikidata': {'requests': 50, 'window': 60},    # 50 req/min
            'default': {'requests': 30, 'window': 60}      # 30 req/min
        }
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def can_make_request(self, service: str = 'default') -> bool:
        """Verifica se pode fazer uma requisição"""
        with self.lock:
            now = time.time()
            service_limits = self.limits.get(service, self.limits['default'])
            window = service_limits['window']
            max_requests = service_limits['requests']
            
            # Remove requisições antigas
            while (self.requests[service] and 
                   now - self.requests[service][0] > window):
                self.requests[service].popleft()
            
            # Verifica se pode fazer nova requisição
            return len(self.requests[service]) < max_requests
    
    def record_request(self, service: str = 'default'):
        """Registra uma requisição"""
        with self.lock:
            self.requests[service].append(time.time())
    
    def wait_if_needed(self, service: str = 'default') -> float:
        """Espera se necessário e retorna tempo de espera"""
        if self.can_make_request(service):
            return 0.0
        
        with self.lock:
            if not self.requests[service]:
                return 0.0
            
            service_limits = self.limits.get(service, self.limits['default'])
            oldest_request = self.requests[service][0]
            wait_time = service_limits['window'] - (time.time() - oldest_request)
            
            if wait_time > 0:
                time.sleep(wait_time)
                return wait_time
            
            return 0.0

# Instância global do rate limiter
rate_limiter = RateLimiter()

def rate_limited(service: str = 'default'):
    """Decorator para aplicar rate limiting a funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = rate_limiter.wait_if_needed(service)
            if wait_time > 0:
                print(f"Rate limit atingido para {service}. Aguardando {wait_time:.1f}s...")
            
            try:
                result = func(*args, **kwargs)
                rate_limiter.record_request(service)
                return result
            except Exception as e:
                rate_limiter.record_request(service)  # Conta mesmo se falhar
                raise e
        
        return wrapper
    return decorator

class SafeRequester:
    """Classe para fazer requisições HTTP de forma segura"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Wikipedia GeoHist/1.0 (https://github.com/user/wikipedia-geohist; contact@example.com) Python/requests'
        })
        
        # Configurações de retry
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    @rate_limited('wikipedia')
    def get_wikipedia(self, url: str, timeout: int = 10) -> requests.Response:
        """Faz requisição para Wikipedia com rate limiting"""
        return self.session.get(url, timeout=timeout)
    
    @rate_limited('wikidata')
    def get_wikidata(self, url: str, timeout: int = 15) -> requests.Response:
        """Faz requisição para Wikidata com rate limiting"""
        return self.session.get(url, timeout=timeout)
    
    @rate_limited('default')
    def get_generic(self, url: str, timeout: int = 10) -> requests.Response:
        """Faz requisição genérica com rate limiting"""
        return self.session.get(url, timeout=timeout)
    
    def close(self):
        """Fecha a sessão"""
        self.session.close()

# Instância global do requester seguro
safe_requester = SafeRequester()

class CircuitBreaker:
    """Circuit breaker para evitar requisições desnecessárias quando serviço está fora"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Verifica se pode executar a operação"""
        with self.lock:
            if self.state == 'CLOSED':
                return True
            elif self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = 'HALF_OPEN'
                    return True
                return False
            else:  # HALF_OPEN
                return True
    
    def record_success(self):
        """Registra sucesso"""
        with self.lock:
            self.failure_count = 0
            self.state = 'CLOSED'
    
    def record_failure(self):
        """Registra falha"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            elif self.state == 'HALF_OPEN':
                self.state = 'OPEN'

# Circuit breakers para diferentes serviços
circuit_breakers = {
    'wikipedia': CircuitBreaker(failure_threshold=3, timeout=120),
    'wikidata': CircuitBreaker(failure_threshold=3, timeout=120),
}

def with_circuit_breaker(service: str):
    """Decorator para aplicar circuit breaker"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = circuit_breakers.get(service)
            if not breaker:
                return func(*args, **kwargs)
            
            if not breaker.can_execute():
                raise Exception(f"Circuit breaker OPEN para {service}")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise e
        
        return wrapper
    return decorator