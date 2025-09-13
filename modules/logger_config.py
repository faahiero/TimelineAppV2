"""
Sistema de logging configurável para o Wikipedia GeoHist
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class WikipediaGeoHistLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._ensure_log_dir()
        self._setup_loggers()
    
    def _ensure_log_dir(self):
        """Cria o diretório de logs se não existir"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_loggers(self):
        """Configura os diferentes loggers"""
        # Logger principal da aplicação
        self.app_logger = self._create_logger(
            'wikipedia_geohist',
            os.path.join(self.log_dir, 'app.log'),
            logging.INFO
        )
        
        # Logger para erros críticos
        self.error_logger = self._create_logger(
            'wikipedia_geohist_errors',
            os.path.join(self.log_dir, 'errors.log'),
            logging.ERROR
        )
        
        # Logger para performance/debug
        self.debug_logger = self._create_logger(
            'wikipedia_geohist_debug',
            os.path.join(self.log_dir, 'debug.log'),
            logging.DEBUG
        )
        
        # Logger para requisições web
        self.web_logger = self._create_logger(
            'wikipedia_geohist_web',
            os.path.join(self.log_dir, 'web_requests.log'),
            logging.INFO
        )
    
    def _create_logger(self, name: str, log_file: str, level: int):
        """Cria um logger configurado"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove handlers existentes para evitar duplicação
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para arquivo com rotação
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        
        # Handler para console (apenas para INFO e acima)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato das mensagens
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        if level <= logging.INFO:
            logger.addHandler(console_handler)
        
        return logger
    
    def log_search(self, search_term: str, success: bool, execution_time: float = None):
        """Log específico para buscas"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Search: '{search_term}' - Status: {status}"
        if execution_time:
            message += f" - Time: {execution_time:.2f}s"
        
        if success:
            self.app_logger.info(message)
        else:
            self.error_logger.error(message)
    
    def log_web_request(self, url: str, status_code: int, response_time: float = None):
        """Log específico para requisições web"""
        message = f"Web Request: {url} - Status: {status_code}"
        if response_time:
            message += f" - Time: {response_time:.2f}s"
        
        if 200 <= status_code < 300:
            self.web_logger.info(message)
        else:
            self.web_logger.warning(message)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log específico para erros"""
        message = f"Error in {context}: {str(error)}"
        self.error_logger.error(message, exc_info=True)
    
    def log_performance(self, operation: str, execution_time: float, details: str = ""):
        """Log específico para performance"""
        message = f"Performance - {operation}: {execution_time:.2f}s"
        if details:
            message += f" - {details}"
        
        self.debug_logger.debug(message)

# Instância global do logger
logger = WikipediaGeoHistLogger()