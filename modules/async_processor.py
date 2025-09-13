"""
Sistema de processamento assíncrono para melhorar performance
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

class AsyncDataProcessor:
    """Processador assíncrono para coleta de dados em lote"""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None
        self.semaphore = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Wikipedia GeoHist/1.0 (https://github.com/user/wikipedia-geohist; contact@example.com) Python/aiohttp'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Faz uma requisição HTTP assíncrona"""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            'url': url,
                            'status': response.status,
                            'content': content,
                            'headers': dict(response.headers)
                        }
                    else:
                        return {
                            'url': url,
                            'status': response.status,
                            'content': None,
                            'error': f'HTTP {response.status}'
                        }
            except asyncio.TimeoutError:
                return {
                    'url': url,
                    'status': 408,
                    'content': None,
                    'error': 'Timeout'
                }
            except Exception as e:
                return {
                    'url': url,
                    'status': 500,
                    'content': None,
                    'error': str(e)
                }
    
    async def process_search_terms_batch(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Processa múltiplos termos de busca em paralelo"""
        tasks = []
        
        for term in search_terms:
            # Cria URL de busca da Wikipedia
            encoded_term = term.replace(' ', '+')
            search_url = f"https://pt.wikipedia.org/w/index.php?search={encoded_term}&title=Especial:Pesquisar&profile=advanced&fulltext=1&ns0=1"
            tasks.append(self.fetch_url(search_url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa os resultados
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'search_term': search_terms[i],
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append({
                    'search_term': search_terms[i],
                    'success': result['status'] == 200,
                    'data': result
                })
        
        return processed_results

class ThreadedProcessor:
    """Processador usando threads para operações CPU-intensivas"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_data_parallel(self, data_list: List[Any], process_func, *args, **kwargs) -> List[Any]:
        """Processa uma lista de dados em paralelo usando threads"""
        futures = []
        
        for data in data_list:
            future = self.executor.submit(process_func, data, *args, **kwargs)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=30)  # 30 segundos timeout
                results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'success': False})
        
        return results
    
    def __del__(self):
        """Cleanup do executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class ProgressTracker:
    """Rastreador de progresso para operações longas"""
    
    def __init__(self, total: int, description: str = "Processando"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.lock = threading.Lock()
    
    def update(self, increment: int = 1):
        """Atualiza o progresso"""
        with self.lock:
            self.current += increment
            self._print_progress()
    
    def _print_progress(self):
        """Imprime o progresso atual"""
        if self.total == 0:
            return
        
        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" - ETA: {eta:.1f}s"
        else:
            eta_str = ""
        
        bar_length = 30
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f'\r{self.description}: |{bar}| {self.current}/{self.total} ({percentage:.1f}%){eta_str}', end='', flush=True)
        
        if self.current >= self.total:
            print()  # Nova linha quando completo

# Funções utilitárias para usar os processadores
async def process_browser_history_async(wikipedia_urls: List[str]) -> List[Dict[str, Any]]:
    """Processa histórico do navegador de forma assíncrona"""
    async with AsyncDataProcessor(max_concurrent=3) as processor:
        return await processor.process_search_terms_batch(wikipedia_urls)

def process_person_data_parallel(person_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Processa dados de pessoas em paralelo"""
    from modules.data_validator import validator
    
    processor = ThreadedProcessor(max_workers=4)
    progress = ProgressTracker(len(person_data_list), "Validando dados")
    
    def validate_with_progress(data):
        try:
            result = validator.sanitize_person_data(data)
            progress.update()
            return result
        except Exception as e:
            progress.update()
            return {'error': str(e), 'original_data': data}
    
    return processor.process_data_parallel(person_data_list, validate_with_progress)