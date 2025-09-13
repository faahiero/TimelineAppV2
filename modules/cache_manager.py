"""
Sistema de cache para otimizar consultas repetidas à Wikipedia/Wikidata
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class CacheManager:
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Cria o diretório de cache se não existir"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, search_term: str) -> str:
        """Gera uma chave única para o termo de busca"""
        return hashlib.md5(search_term.lower().encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Retorna o caminho do arquivo de cache"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Verifica se o cache ainda é válido baseado no TTL"""
        if not os.path.exists(cache_path):
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            return datetime.now() - cached_time < timedelta(hours=self.ttl_hours)
        except:
            return False
    
    def get(self, search_term: str) -> Optional[Dict[Any, Any]]:
        """Recupera dados do cache se válidos"""
        cache_key = self._get_cache_key(search_term)
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                return cache_data.get('data')
            except:
                pass
        
        return None
    
    def set(self, search_term: str, data: Dict[Any, Any]):
        """Armazena dados no cache"""
        cache_key = self._get_cache_key(search_term)
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'search_term': search_term,
            'data': data
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")
    
    def clear_expired(self):
        """Remove arquivos de cache expirados"""
        if not os.path.exists(self.cache_dir):
            return
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                cache_path = os.path.join(self.cache_dir, filename)
                if not self._is_cache_valid(cache_path):
                    try:
                        os.remove(cache_path)
                    except:
                        pass
    
    def clear_all(self):
        """Remove todo o cache"""
        if not os.path.exists(self.cache_dir):
            return
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except:
                    pass

# Instância global do cache
cache_manager = CacheManager()