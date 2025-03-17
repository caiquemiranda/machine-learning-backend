import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

from ..config import Config

class Logger:
    """
    Classe para configuração e gerenciamento de logs da aplicação.
    Permite configurar logs para diferentes componentes com níveis de log personalizados.
    """
    
    def __init__(self, nome_app=None, nivel=logging.INFO, formato=None, arquivo_log=None):
        """
        Inicializa o logger com configurações personalizadas.
        
        Args:
            nome_app (str, optional): Nome do componente/aplicação para o logger. 
                                     Se None, usa o nome do módulo chamador.
            nivel (int, optional): Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            formato (str, optional): Formato da mensagem de log. Se None, usa o formato padrão.
            arquivo_log (str, optional): Caminho para o arquivo de log. 
                                        Se None, usa o diretório padrão de logs.
        """
        # Criar diretório de logs se não existir
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        # Definir nome do logger
        self.nome_app = nome_app or self._obter_nome_modulo_chamador()
        
        # Definir formato do log
        self.formato = formato or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Definir arquivo de log
        if arquivo_log is None:
            data_atual = datetime.now().strftime('%Y-%m-%d')
            self.arquivo_log = os.path.join(Config.LOGS_DIR, f"{self.nome_app}_{data_atual}.log")
        else:
            self.arquivo_log = arquivo_log
        
        # Configurar o logger
        self.logger = logging.getLogger(self.nome_app)
        self.logger.setLevel(nivel)
        
        # Remover handlers existentes para evitar duplicação
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Criar formatador
        formatter = logging.Formatter(self.formato)
        
        # Adicionar handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Adicionar handler para arquivo com rotação
        file_handler = RotatingFileHandler(
            self.arquivo_log, 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _obter_nome_modulo_chamador(self):
        """
        Obtém o nome do módulo que chamou o logger.
        
        Returns:
            str: Nome do módulo chamador
        """
        import inspect
        frame = inspect.stack()[2]
        module = inspect.getmodule(frame[0])
        if module:
            return module.__name__
        return "app"
    
    def get_logger(self):
        """
        Retorna a instância configurada do logger.
        
        Returns:
            Logger: Instância do logger configurada
        """
        return self.logger

# Função para obter um logger configurado
def get_logger(nome_app=None, nivel=logging.INFO):
    """
    Função auxiliar para obter um logger configurado.
    
    Args:
        nome_app (str, optional): Nome do componente/aplicação para o logger.
        nivel (int, optional): Nível de log.
        
    Returns:
        Logger: Instância do logger configurada
    """
    logger_manager = Logger(nome_app=nome_app, nivel=nivel)
    return logger_manager.get_logger() 