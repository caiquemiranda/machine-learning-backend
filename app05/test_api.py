#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from fastapi.testclient import TestClient
import os
import json
import numpy as np
from main import app, modelo, criar_pipeline

# Cliente de teste
client = TestClient(app)

class TestImoveisAPI(unittest.TestCase):
    """Testes para a API de previsão de preços de imóveis"""
    
    def setUp(self):
        """Setup para cada teste"""
        # Reinicia o modelo para um estado limpo
        self.modelo_original = modelo
    
    def tearDown(self):
        """Cleanup após cada teste"""
        pass
    
    def test_index_endpoint(self):
        """Testa se o endpoint raiz responde corretamente"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("mensagem", response.json())
    
    def test_status_endpoint(self):
        """Testa se o endpoint de status retorna as informações corretas"""
        response = client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verifica se todos os campos esperados estão presentes
        self.assertIn("modelo_salvo", data)
        self.assertIn("modelo_carregado", data)
        self.assertIn("features_suportadas", data)
        self.assertIn("estatisticas_api", data)
    
    def test_previsao_sem_modelo_treinado(self):
        """Testa a resposta da API quando tenta fazer previsão sem modelo treinado"""
        # Cria um novo pipeline não treinado
        global modelo
        modelo = criar_pipeline()
        
        # Tenta fazer previsão
        response = client.post(
            "/prever", 
            json={"area": 120, "quartos": 3, "banheiros": 2}
        )
        
        # Deve falhar com status 400
        self.assertEqual(response.status_code, 400)
        self.assertIn("O modelo ainda não foi treinado", response.json()["detail"])
        
        # Restaura o modelo original
        modelo = self.modelo_original
    
    def test_validacao_entrada_previsao(self):
        """Testa a validação de entrada para o endpoint de previsão"""
        # Testa com área negativa (deve falhar)
        response = client.post(
            "/prever", 
            json={"area": -100}
        )
        self.assertEqual(response.status_code, 422)
        
        # Testa com área muito grande (deve falhar)
        response = client.post(
            "/prever", 
            json={"area": 20000}
        )
        self.assertEqual(response.status_code, 422)
        
        # Testa com quartos muito grande (deve falhar)
        response = client.post(
            "/prever", 
            json={"area": 100, "quartos": 50}
        )
        self.assertEqual(response.status_code, 422)
        
        # Testa com proporção inválida (deve falhar)
        response = client.post(
            "/prever", 
            json={"area": 20, "quartos": 5}
        )
        self.assertEqual(response.status_code, 422)
    
    def test_treinar_e_prever(self):
        """Testa o fluxo completo de treinar o modelo e fazer uma previsão"""
        # Dados de treinamento
        dados_treino = {
            "features": [
                {"area": 70, "quartos": 2, "banheiros": 1},
                {"area": 100, "quartos": 3, "banheiros": 1},
                {"area": 120, "quartos": 3, "banheiros": 2},
                {"area": 150, "quartos": 4, "banheiros": 2},
                {"area": 200, "quartos": 4, "banheiros": 3}
            ],
            "precos": [600000, 850000, 1000000, 1250000, 1600000]
        }
        
        # Treina o modelo
        response_treino = client.post("/treinar", json=dados_treino)
        self.assertEqual(response_treino.status_code, 200)
        self.assertIn("r2_score", response_treino.json())
        
        # Faz a previsão
        response_previsao = client.post(
            "/prever", 
            json={"area": 130, "quartos": 3, "banheiros": 2}
        )
        
        # Verifica a resposta
        self.assertEqual(response_previsao.status_code, 200)
        data = response_previsao.json()
        self.assertIn("preco_previsto", data)
        self.assertIn("faixa_confianca", data)
        self.assertIn("request_id", data)
        self.assertIn("timestamp", data)
        
        # Verifica se o preço previsto é razoável (entre 1M e 1.3M)
        self.assertGreater(data["preco_previsto"], 1000000)
        self.assertLess(data["preco_previsto"], 1300000)
    
    def test_validacao_treino(self):
        """Testa a validação de dados para o endpoint de treinamento"""
        # Testa com lista de features vazia
        response = client.post(
            "/treinar", 
            json={"features": [], "precos": []}
        )
        self.assertEqual(response.status_code, 400)
        
        # Testa com número diferente de features e preços
        response = client.post(
            "/treinar", 
            json={
                "features": [{"area": 100}, {"area": 200}],
                "precos": [500000]
            }
        )
        self.assertEqual(response.status_code, 400)
        
        # Testa com preço negativo
        response = client.post(
            "/treinar", 
            json={
                "features": [{"area": 100}],
                "precos": [-500000]
            }
        )
        self.assertEqual(response.status_code, 400)
        
        # Testa com feature desconhecida
        response = client.post(
            "/treinar", 
            json={
                "features": [{"area": 100, "feature_invalida": 10}],
                "precos": [500000]
            }
        )
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main() 