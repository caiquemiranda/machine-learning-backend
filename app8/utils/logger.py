#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time
from logging.handlers import RotatingFileHandler

class Logger:
    """
    Classe para gerenciar logs da aplicação
    """
    def __init__(self, nome_app='imoveis-api', nivel=logging.INFO):
        self.logger = None
        self.nome_app = nome_app
        self.nivel = nivel
        self.log_dir = 'logs'
        self.configurar()
    
    def configurar(self):
        """Configura o logger com handlers para arquivo e console"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Cria o logger
        self.logger = logging.getLogger(self.nome_app)
        self.logger.setLevel(self.nivel)
        
        # Remove handlers existentes para evitar duplicação
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Cria o formato do log
        formato = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para arquivo com rotação (máximo 10MB por arquivo, 5 backups)
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, 'api.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formato)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formato)
        
        # Adiciona os handlers ao logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Retorna o objeto logger configurado"""
        return self.logger 