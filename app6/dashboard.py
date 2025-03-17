#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import json
import os
import time

# Configurações da página
st.set_page_config(
    page_title="Dashboard - Previsão de Preços de Imóveis",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes
API_URL = "http://localhost:8000"
ENDPOINTS = {
    "status": f"{API_URL}/status",
    "previsoes": f"{API_URL}/previsoes",
    "previsao": f"{API_URL}/prever"
}

# Função para carregar dados da API
@st.cache_data(ttl=5)  # Cache com validade de 5 segundos
def carregar_status():
    try:
        response = requests.get(ENDPOINTS["status"])
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar status da API: {e}")
        return None

@st.cache_data(ttl=5)  # Cache com validade de 5 segundos
def carregar_previsoes():
    try:
        response = requests.get(ENDPOINTS["previsoes"])
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar previsões: {e}")
        return []

def realizar_previsao(dados):
    try:
        response = requests.post(ENDPOINTS["previsao"], json=dados)
        return response.json()
    except Exception as e:
        st.error(f"Erro ao realizar previsão: {e}")
        return None

# Função para formatar timestamp
def formatar_data(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return timestamp_str

# Sidebar: Informações da API
st.sidebar.title("API de Previsões")
status_api = carregar_status()

if status_api:
    st.sidebar.metric("Status do Modelo", 
                     "Treinado ✅" if status_api.get("modelo_carregado") else "Não treinado ❌")
    
    estatisticas = status_api.get("estatisticas_api", {})
    
    # Uptime
    uptime_segundos = estatisticas.get("uptime_seconds", 0)
    dias = uptime_segundos // (24 * 3600)
    horas = (uptime_segundos % (24 * 3600)) // 3600
    minutos = (uptime_segundos % 3600) // 60
    
    st.sidebar.metric("Uptime", f"{int(dias)}d {int(horas)}h {int(minutos)}m")
    
    # Métricas de requisições
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total de Requisições", estatisticas.get("total_requests", 0))
    col2.metric("Requisições com Sucesso", estatisticas.get("successful_requests", 0))
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Previsões Realizadas", estatisticas.get("previsoes_realizadas", 0))
    col2.metric("Treinamentos", estatisticas.get("treinamentos_realizados", 0))
    
    # Último erro
    ultimo_erro = estatisticas.get("ultimo_erro")
    if ultimo_erro:
        st.sidebar.error("Último Erro:")
        st.sidebar.text(f"Timestamp: {formatar_data(ultimo_erro.get('timestamp', ''))}")
        st.sidebar.text(f"Erro: {ultimo_erro.get('error', 'Desconhecido')}")
else:
    st.sidebar.error("API não está disponível. Verifique se a API está em execução.")

# Sidebar: Ferramenta de previsão
st.sidebar.title("Fazer Nova Previsão")

with st.sidebar.form("previsao_form"):
    area = st.number_input("Área (m²)", min_value=10.0, max_value=10000.0, value=100.0, step=10.0)
    quartos = st.number_input("Quartos", min_value=0, max_value=10, value=2, step=1)
    banheiros = st.number_input("Banheiros", min_value=0, max_value=10, value=1, step=1)
    idade = st.number_input("Idade do Imóvel (anos)", min_value=0, max_value=100, value=5, step=1)
    
    submit_button = st.form_submit_button("Prever Preço")
    
    if submit_button:
        dados_previsao = {
            "area": area,
            "quartos": quartos,
            "banheiros": banheiros,
            "idade_imovel": idade
        }
        
        with st.spinner("Realizando previsão..."):
            resultado = realizar_previsao(dados_previsao)
            
        if resultado:
            preco = resultado.get("preco_previsto", 0)
            faixa = resultado.get("faixa_confianca", [0, 0])
            
            st.success(f"Preço Previsto: R$ {preco:,.2f}")
            st.info(f"Faixa de Confiança: R$ {faixa[0]:,.2f} a R$ {faixa[1]:,.2f}")
            st.success("Previsão realizada com sucesso! Atualize o dashboard para ver nos gráficos.")

# Conteúdo principal
st.title("Dashboard - Previsão de Preços de Imóveis")

# Carrega o histórico de previsões
previsoes = carregar_previsoes()

if not previsoes:
    st.warning("Não há previsões para exibir. Faça algumas previsões para visualizar os gráficos.")
else:
    # Converte para DataFrame
    df_previsoes = pd.DataFrame([
        {
            "id": p.get("request_id"),
            "timestamp": p.get("timestamp"),
            "area": p.get("input", {}).get("area"),
            "quartos": p.get("input", {}).get("quartos"),
            "banheiros": p.get("input", {}).get("banheiros"),
            "idade_imovel": p.get("input", {}).get("idade_imovel"),
            "preco_previsto": p.get("preco_previsto"),
            "faixa_inferior": p.get("faixa_confianca", [0, 0])[0],
            "faixa_superior": p.get("faixa_confianca", [0, 0])[1],
            "data_formatada": formatar_data(p.get("timestamp", ""))
        }
        for p in previsoes
    ])
    
    # Converte para datetime
    df_previsoes["timestamp"] = pd.to_datetime(df_previsoes["timestamp"])
    
    # Métricas Principais
    st.subheader("Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Previsões", len(df_previsoes))
    col2.metric("Preço Médio", f"R$ {df_previsoes['preco_previsto'].mean():,.2f}")
    col3.metric("Maior Preço", f"R$ {df_previsoes['preco_previsto'].max():,.2f}")
    col4.metric("Menor Preço", f"R$ {df_previsoes['preco_previsto'].min():,.2f}")
    
    # Gráficos
    st.subheader("Visualizações")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Distribuição de Preços", "Correlações", "Histórico de Previsões", "Dados Detalhados"])
    
    with tab1:
        st.subheader("Distribuição dos Preços Previstos")
        
        # Histograma de preços
        fig = px.histogram(
            df_previsoes, 
            x="preco_previsto",
            nbins=30,
            title="Distribuição dos Preços Previstos",
            labels={"preco_previsto": "Preço Previsto (R$)", "count": "Frequência"},
            color_discrete_sequence=["#3366CC"]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Boxplot por número de quartos
        if df_previsoes["quartos"].notna().sum() > 0:
            fig = px.box(
                df_previsoes,
                x="quartos",
                y="preco_previsto",
                title="Preços por Número de Quartos",
                labels={"quartos": "Quartos", "preco_previsto": "Preço Previsto (R$)"}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Correlações entre Características e Preços")
        
        # Scatter plot: Área x Preço
        fig = px.scatter(
            df_previsoes,
            x="area",
            y="preco_previsto",
            size="quartos" if "quartos" in df_previsoes.columns else None,
            color="banheiros" if "banheiros" in df_previsoes.columns else None,
            title="Relação entre Área e Preço Previsto",
            labels={
                "area": "Área (m²)",
                "preco_previsto": "Preço Previsto (R$)",
                "quartos": "Quartos",
                "banheiros": "Banheiros"
            },
            trendline="ols"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap de correlação
        numeric_cols = df_previsoes.select_dtypes(include=[np.number]).columns
        corr_matrix = df_previsoes[numeric_cols].corr()
        
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            title="Matriz de Correlação"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Histórico de Previsões ao Longo do Tempo")
        
        # Previsões ao longo do tempo
        fig = px.line(
            df_previsoes.sort_values("timestamp"),
            x="timestamp",
            y="preco_previsto",
            title="Preços Previstos ao Longo do Tempo",
            labels={"timestamp": "Data/Hora", "preco_previsto": "Preço Previsto (R$)"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Média móvel de preços
        df_previsoes_ordenado = df_previsoes.sort_values("timestamp")
        df_previsoes_ordenado["media_movel"] = df_previsoes_ordenado["preco_previsto"].rolling(window=5).mean()
        
        fig = px.line(
            df_previsoes_ordenado,
            x="timestamp",
            y=["preco_previsto", "media_movel"],
            title="Preços Previstos com Média Móvel (5 previsões)",
            labels={
                "timestamp": "Data/Hora", 
                "value": "Preço (R$)",
                "variable": "Tipo"
            }
        )
        fig.update_layout(legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Dados Detalhados")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            min_preco = st.slider("Preço Mínimo", 
                               float(df_previsoes["preco_previsto"].min()), 
                               float(df_previsoes["preco_previsto"].max()), 
                               float(df_previsoes["preco_previsto"].min()))
        with col2:
            max_preco = st.slider("Preço Máximo", 
                               float(df_previsoes["preco_previsto"].min()), 
                               float(df_previsoes["preco_previsto"].max()), 
                               float(df_previsoes["preco_previsto"].max()))
        
        # Filtra os dados
        df_filtrado = df_previsoes[
            (df_previsoes["preco_previsto"] >= min_preco) & 
            (df_previsoes["preco_previsto"] <= max_preco)
        ]
        
        # Tabela de dados
        st.dataframe(
            df_filtrado[["data_formatada", "area", "quartos", "banheiros", "idade_imovel", "preco_previsto"]].rename(
                columns={
                    "data_formatada": "Data/Hora",
                    "area": "Área (m²)",
                    "quartos": "Quartos",
                    "banheiros": "Banheiros",
                    "idade_imovel": "Idade (anos)",
                    "preco_previsto": "Preço Previsto (R$)"
                }
            ),
            use_container_width=True
        )

# Footer
st.markdown("---")
st.caption("Dashboard de Previsão de Preços de Imóveis - App 6 - Desenvolvido com Streamlit")

# Atualização automática
auto_refresh = st.sidebar.checkbox("Atualização Automática (10s)", value=False)

if auto_refresh:
    st.empty()
    time.sleep(10)
    st.experimental_rerun() 