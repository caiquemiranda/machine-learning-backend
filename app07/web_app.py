#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json
from datetime import datetime
import time
from typing import Dict, List, Any, Optional, Tuple
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="Previsão de Preços de Imóveis",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL base da API
API_URL = "http://localhost:8000"

# Função para fazer requisições à API
def fazer_requisicao(endpoint, metodo="GET", dados=None, params=None):
    """
    Realiza uma requisição à API.
    
    Args:
        endpoint: Caminho do endpoint na API
        metodo: Método HTTP (GET, POST, etc)
        dados: Dados para envio (para POST, PUT)
        params: Parâmetros para query string
        
    Returns:
        Resposta da API ou None em caso de erro
    """
    url = f"{API_URL}{endpoint}"
    
    try:
        if metodo == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif metodo == "POST":
            response = requests.post(url, json=dados, timeout=10)
        else:
            st.error(f"Método HTTP não suportado: {metodo}")
            return None
            
        # Verifica se a requisição foi bem-sucedida
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão. Verifique se a API está rodando.")
    except requests.exceptions.Timeout:
        st.error("Tempo de requisição esgotado. A API pode estar sobrecarregada.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP: {e}")
        try:
            st.error(f"Detalhes: {response.json()}")
        except:
            pass
    except Exception as e:
        st.error(f"Erro ao fazer requisição: {e}")
    
    return None

# Função para verificar se a API está online
def verificar_status_api():
    """Verifica se a API está online e retorna informações básicas"""
    try:
        response = fazer_requisicao("/")
        if response:
            return True, response
        return False, None
    except:
        return False, None


# Funções para as diferentes páginas da aplicação
def pagina_inicial():
    """Página inicial com informações sobre a aplicação"""
    st.title("🏠 Sistema de Previsão de Preços de Imóveis")
    
    # Verifica status da API
    with st.spinner("Verificando conexão com a API..."):
        api_online, info = verificar_status_api()
    
    if not api_online:
        st.error("❌ API offline. Por favor, inicie a API para usar este aplicativo.")
        st.info("Comando para iniciar a API: `python main.py`")
        return
    
    st.success("✅ API conectada e funcionando!")
    
    # Obtém status detalhado
    status_data = fazer_requisicao("/status")
    
    if status_data:
        # Informações do modelo
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informações do Modelo")
            model_info = {
                "Modelo treinado": "✅ Sim" if status_data["modelo_carregado"] else "❌ Não",
                "Modelo salvo em disco": "✅ Sim" if status_data["modelo_salvo"] else "❌ Não",
                "Features suportadas": ", ".join(status_data["features_suportadas"]),
                "Amostras de treinamento": status_data.get("numero_amostras_treinamento", "N/A")
            }
            st.table(pd.DataFrame(list(model_info.items()), 
                                 columns=["Atributo", "Valor"]))
        
        with col2:
            st.subheader("Estatísticas da API")
            api_stats = status_data["estatisticas_api"]
            
            # Calcula tempo online em formato legível
            uptime_segundos = api_stats.get("uptime_seconds", 0)
            horas, resto = divmod(uptime_segundos, 3600)
            minutos, segundos = divmod(resto, 60)
            uptime_formatado = f"{int(horas)}h {int(minutos)}m {int(segundos)}s"
            
            api_metrics = {
                "Total de requisições": api_stats["total_requests"],
                "Requisições com sucesso": api_stats["successful_requests"],
                "Requisições com erro": api_stats["failed_requests"],
                "Tempo online": uptime_formatado
            }
            
            st.table(pd.DataFrame(list(api_metrics.items()), 
                                 columns=["Métrica", "Valor"]))
        
        # Estatísticas do banco de dados
        st.subheader("Estatísticas do Banco de Dados")
        db_metrics = status_data["metricas_banco_dados"]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Treinamentos", db_metrics.get("total_treinamentos", 0))
        col2.metric("Total de Previsões", db_metrics.get("total_previsoes", 0))
        col3.metric("Total de Dados de Treinamento", db_metrics.get("total_dados_treinamento", 0))
        
        # Último treinamento
        ultimo_treinamento = db_metrics.get("ultimo_treinamento")
        if ultimo_treinamento:
            st.subheader("Último Treinamento")
            
            # Linha do tempo
            data_formatada = datetime.fromisoformat(ultimo_treinamento["timestamp"]).strftime("%d/%m/%Y %H:%M:%S")
            st.write(f"**Data:** {data_formatada}")
            
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            col1.metric("R² Score", f"{ultimo_treinamento['r2_score']:.4f}")
            col2.metric("RMSE", f"{ultimo_treinamento.get('rmse', 'N/A'):.2f}")
            col3.metric("MAE", f"{ultimo_treinamento.get('mae', 'N/A'):.2f}")
            
            # Coeficientes
            if "coeficientes" in ultimo_treinamento:
                st.subheader("Coeficientes do Modelo")
                coefs = ultimo_treinamento["coeficientes"]
                coef_df = pd.DataFrame({
                    "Feature": list(coefs.keys()),
                    "Coeficiente": list(coefs.values())
                })
                
                # Cria gráfico de barras para coeficientes
                fig = px.bar(
                    coef_df, 
                    x="Feature", 
                    y="Coeficiente",
                    title="Importância das Features no Modelo",
                    color="Coeficiente",
                    color_continuous_scale="RdBu",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Explicação sobre a aplicação
    st.subheader("Sobre este Aplicativo")
    st.markdown("""
    Este aplicativo permite:
    
    1. **Treinar** um modelo de previsão de preços de imóveis com seus próprios dados
    2. **Prever** o preço de novos imóveis
    3. **Visualizar** estatísticas e histórico de previsões
    4. **Analisar** o histórico de treinamentos e modelos
    
    Utilize o menu lateral para navegar entre as diferentes funcionalidades.
    """)


def pagina_previsao():
    """Página para fazer previsões de preços"""
    st.title("🔮 Prever Preço de Imóvel")
    
    # Verifica se o modelo está treinado
    status_data = fazer_requisicao("/status")
    if not status_data or not status_data.get("modelo_carregado"):
        st.warning("⚠️ O modelo ainda não foi treinado. Por favor, treine o modelo primeiro.")
        if st.button("Ir para página de treinamento"):
            st.session_state.page = "treinar"
            st.experimental_rerun()
        return
    
    st.markdown("### Informe as características do imóvel")
    
    # Formulário para entrada de dados
    with st.form(key="previsao_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            area = st.number_input("Área (m²)", min_value=1.0, max_value=10000.0, value=100.0, step=10.0)
            quartos = st.number_input("Número de Quartos", min_value=0, max_value=20, value=2, step=1)
        
        with col2:
            banheiros = st.number_input("Número de Banheiros", min_value=0, max_value=20, value=1, step=1)
            idade_imovel = st.number_input("Idade do Imóvel (anos)", min_value=0, max_value=200, value=5, step=1)
        
        submit_button = st.form_submit_button(label="Prever Preço")
    
    # Quando o botão é clicado, faz a previsão
    if submit_button:
        with st.spinner("Calculando previsão..."):
            # Prepara dados para a requisição
            dados_previsao = {
                "area": area,
                "quartos": quartos,
                "banheiros": banheiros,
                "idade_imovel": idade_imovel
            }
            
            # Faz a requisição à API
            resultado = fazer_requisicao("/prever", metodo="POST", dados=dados_previsao)
            
            if resultado:
                # Exibe o resultado
                st.success("Previsão calculada!")
                
                # Exibe o preço previsto com formatação
                preco = resultado["preco_previsto"]
                faixa_inferior, faixa_superior = resultado["faixa_confianca"]
                
                # Mostra resultado principal
                st.markdown(f"## Preço Previsto: R$ {preco:,.2f}")
                
                # Informações adicionais
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Faixa de Preço")
                    st.markdown(f"**Mínimo:** R$ {faixa_inferior:,.2f}")
                    st.markdown(f"**Máximo:** R$ {faixa_superior:,.2f}")
                
                with col2:
                    # Informações da previsão
                    st.subheader("Detalhes")
                    st.markdown(f"**ID da Requisição:** {resultado['request_id']}")
                    st.markdown(f"**Data/Hora:** {resultado['timestamp']}")
                
                # Visualização
                fig = go.Figure()
                
                # Adiciona o valor previsto como ponto
                fig.add_trace(go.Scatter(
                    x=[0], 
                    y=[preco],
                    mode='markers',
                    name='Preço Previsto',
                    marker=dict(size=15, color='green')
                ))
                
                # Adiciona a faixa de confiança como área
                fig.add_trace(go.Scatter(
                    x=[0, 0],
                    y=[faixa_inferior, faixa_superior],
                    mode='lines',
                    name='Faixa de Confiança',
                    line=dict(width=5, color='rgba(0,100,80,0.5)')
                ))
                
                # Configurações do layout
                fig.update_layout(
                    title="Previsão de Preço com Faixa de Confiança",
                    xaxis=dict(
                        title="",
                        showticklabels=False
                    ),
                    yaxis=dict(
                        title="Preço (R$)"
                    ),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)


def pagina_treinamento():
    """Página para treinar o modelo"""
    st.title("🧠 Treinar Modelo")
    
    st.markdown("""
    Nesta página você pode treinar o modelo com seus próprios dados.
    Você pode fornecer dados manualmente ou usar um conjunto de dados de exemplo.
    """)
    
    # Opções de entrada de dados
    input_method = st.radio(
        "Escolha como deseja fornecer os dados:",
        ("Usar dados de exemplo", "Entrada manual", "Upload de CSV")
    )
    
    # Dados de exemplo pré-definidos
    if input_method == "Usar dados de exemplo":
        st.info("Estes são dados fictícios para testar o modelo")
        
        # Cria DataFrame de exemplo
        dados_exemplo = pd.DataFrame({
            "area": [70, 90, 120, 150, 180, 200, 250, 300, 85, 100],
            "quartos": [1, 2, 3, 3, 4, 4, 5, 5, 2, 2],
            "banheiros": [1, 1, 2, 2, 3, 3, 4, 4, 1, 1],
            "idade_imovel": [15, 10, 5, 3, 7, 2, 1, 0, 20, 12],
            "preco": [200000, 300000, 400000, 500000, 600000, 700000, 950000, 1100000, 280000, 320000]
        })
        
        st.write(dados_exemplo)
        
        # Botão para treinar com dados de exemplo
        if st.button("Treinar com Dados de Exemplo"):
            with st.spinner("Treinando modelo..."):
                # Prepare dados para a API
                features = []
                for _, row in dados_exemplo.iterrows():
                    features.append({
                        "area": float(row["area"]),
                        "quartos": int(row["quartos"]),
                        "banheiros": int(row["banheiros"]),
                        "idade_imovel": int(row["idade_imovel"])
                    })
                
                dados_treinamento = {
                    "features": features,
                    "precos": dados_exemplo["preco"].tolist()
                }
                
                # Faz a requisição de treinamento
                resultado = fazer_requisicao("/treinar", metodo="POST", dados=dados_treinamento)
                
                if resultado:
                    st.success("✅ Modelo treinado com sucesso!")
                    
                    # Mostra estatísticas
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Amostras", resultado["num_amostras"])
                    col2.metric("R² Score", f"{resultado['r2_score']:.4f}")
                    col3.metric("RMSE", f"{resultado.get('rmse', 0):.2f}")
                    
                    st.balloons()
    
    # Entrada manual de dados
    elif input_method == "Entrada manual":
        st.markdown("### Digite os dados para treinamento")
        
        # Número de amostras
        num_samples = st.number_input("Número de amostras", min_value=3, max_value=50, value=5)
        
        # Cria DataFrame vazio
        if "train_data" not in st.session_state or len(st.session_state.train_data) != num_samples:
            # Inicializa com valores padrão
            st.session_state.train_data = pd.DataFrame({
                "area": [100] * num_samples,
                "quartos": [2] * num_samples,
                "banheiros": [1] * num_samples,
                "idade_imovel": [5] * num_samples,
                "preco": [300000] * num_samples
            })
        
        # Interface para editar dados
        st.markdown("#### Edite os valores abaixo:")
        edited_df = st.data_editor(
            st.session_state.train_data,
            num_rows="fixed",
            column_config={
                "area": st.column_config.NumberColumn("Área (m²)", min_value=10, max_value=1000, step=10),
                "quartos": st.column_config.NumberColumn("Quartos", min_value=0, max_value=10, step=1),
                "banheiros": st.column_config.NumberColumn("Banheiros", min_value=0, max_value=10, step=1),
                "idade_imovel": st.column_config.NumberColumn("Idade (anos)", min_value=0, max_value=100, step=1),
                "preco": st.column_config.NumberColumn("Preço (R$)", min_value=50000, max_value=5000000, step=10000, format="R$ %d")
            }
        )
        
        st.session_state.train_data = edited_df
        
        # Botão para treinar com dados manuais
        if st.button("Treinar com Dados Manuais"):
            with st.spinner("Treinando modelo..."):
                # Prepara dados para a API
                features = []
                for _, row in edited_df.iterrows():
                    features.append({
                        "area": float(row["area"]),
                        "quartos": int(row["quartos"]),
                        "banheiros": int(row["banheiros"]),
                        "idade_imovel": int(row["idade_imovel"])
                    })
                
                dados_treinamento = {
                    "features": features,
                    "precos": edited_df["preco"].tolist()
                }
                
                # Faz a requisição de treinamento
                resultado = fazer_requisicao("/treinar", metodo="POST", dados=dados_treinamento)
                
                if resultado:
                    st.success("✅ Modelo treinado com sucesso!")
                    
                    # Mostra estatísticas
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Amostras", resultado["num_amostras"])
                    col2.metric("R² Score", f"{resultado['r2_score']:.4f}")
                    col3.metric("RMSE", f"{resultado.get('rmse', 0):.2f}")
                    
                    st.balloons()
    
    # Upload de CSV
    else:
        st.markdown("### Faça upload de um arquivo CSV")
        st.markdown("""
        O arquivo CSV deve conter as colunas:
        - `area` (obrigatória)
        - `quartos` (opcional)
        - `banheiros` (opcional)
        - `idade_imovel` (opcional)
        - `preco` (obrigatória)
        """)
        
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
        
        if uploaded_file is not None:
            try:
                # Lê o arquivo CSV
                data = pd.read_csv(uploaded_file)
                
                # Verifica colunas obrigatórias
                required_cols = ["area", "preco"]
                if not all(col in data.columns for col in required_cols):
                    st.error(f"O CSV deve conter as colunas: {', '.join(required_cols)}")
                else:
                    st.write("Dados carregados:")
                    st.write(data)
                    
                    # Botão para treinar com dados do CSV
                    if st.button("Treinar com Dados do CSV"):
                        with st.spinner("Treinando modelo..."):
                            # Prepara dados para a API
                            features = []
                            for _, row in data.iterrows():
                                feature = {"area": float(row["area"])}
                                
                                # Adiciona colunas opcionais se presentes
                                for col in ["quartos", "banheiros", "idade_imovel"]:
                                    if col in data.columns:
                                        feature[col] = int(row[col]) if not pd.isna(row[col]) else None
                                
                                features.append(feature)
                            
                            dados_treinamento = {
                                "features": features,
                                "precos": data["preco"].tolist()
                            }
                            
                            # Faz a requisição de treinamento
                            resultado = fazer_requisicao("/treinar", metodo="POST", dados=dados_treinamento)
                            
                            if resultado:
                                st.success("✅ Modelo treinado com sucesso!")
                                
                                # Mostra estatísticas
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Amostras", resultado["num_amostras"])
                                col2.metric("R² Score", f"{resultado['r2_score']:.4f}")
                                col3.metric("RMSE", f"{resultado.get('rmse', 0):.2f}")
                                
                                st.balloons()
            
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")


def pagina_historico():
    """Página para visualizar histórico de previsões e treinamentos"""
    st.title("📊 Histórico e Estatísticas")
    
    # Abas para diferentes tipos de histórico
    tab1, tab2 = st.tabs(["Histórico de Previsões", "Histórico de Treinamentos"])
    
    with tab1:
        st.subheader("Histórico de Previsões")
        
        # Configurações de paginação
        limit = st.slider("Número de previsões a exibir", min_value=5, max_value=100, value=20)
        offset = st.number_input("Offset", min_value=0, value=0)
        
        # Botão para atualizar
        if st.button("Atualizar Histórico de Previsões"):
            with st.spinner("Carregando dados..."):
                previsoes = fazer_requisicao("/previsoes", params={"limit": limit, "offset": offset})
                
                if previsoes:
                    if len(previsoes) == 0:
                        st.info("Nenhuma previsão encontrada.")
                    else:
                        # Converte para DataFrame para facilitar a visualização
                        df_previsoes = []
                        for p in previsoes:
                            df_previsoes.append({
                                "ID": p["request_id"][:8],  # Trunca para melhor visualização
                                "Data": datetime.fromisoformat(p["timestamp"]).strftime("%d/%m/%Y %H:%M"),
                                "Área": p["input"]["area"],
                                "Quartos": p["input"].get("quartos", "-"),
                                "Banheiros": p["input"].get("banheiros", "-"),
                                "Idade": p["input"].get("idade_imovel", "-"),
                                "Preço Previsto": f"R$ {p['preco_previsto']:,.2f}",
                                "Preço Mínimo": f"R$ {p['faixa_confianca'][0]:,.2f}",
                                "Preço Máximo": f"R$ {p['faixa_confianca'][1]:,.2f}"
                            })
                        
                        df = pd.DataFrame(df_previsoes)
                        st.write(df)
                        
                        # Gráfico com as últimas previsões
                        st.subheader("Últimas Previsões")
                        
                        # Prepara dados para o gráfico
                        for i, p in enumerate(previsoes[:10]):  # Limita a 10 para o gráfico
                            previsoes[i]["index"] = i
                        
                        # Cria um gráfico com Plotly
                        fig = go.Figure()
                        
                        # Adiciona pontos para cada previsão
                        x_values = [p["index"] for p in previsoes[:10]]
                        y_values = [p["preco_previsto"] for p in previsoes[:10]]
                        
                        # Adiciona o traço principal
                        fig.add_trace(go.Scatter(
                            x=x_values,
                            y=y_values,
                            mode='lines+markers',
                            name='Preço Previsto',
                            line=dict(color='royalblue', width=3),
                            marker=dict(size=10)
                        ))
                        
                        # Adiciona faixa de confiança
                        y_lower = [p["faixa_confianca"][0] for p in previsoes[:10]]
                        y_upper = [p["faixa_confianca"][1] for p in previsoes[:10]]
                        
                        fig.add_trace(go.Scatter(
                            x=x_values + x_values[::-1],
                            y=y_upper + y_lower[::-1],
                            fill='toself',
                            fillcolor='rgba(0,176,246,0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            name='Faixa de Confiança'
                        ))
                        
                        # Configurações do layout
                        fig.update_layout(
                            title="Histórico de Previsões Recentes",
                            xaxis_title="Índice",
                            yaxis_title="Preço (R$)",
                            legend=dict(
                                x=0.01,
                                y=0.99,
                                traceorder="normal",
                                bgcolor='rgba(255,255,255,0.5)',
                            ),
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Histórico de Treinamentos")
        
        # Configurações de paginação
        limit_treino = st.slider("Número de treinamentos a exibir", min_value=1, max_value=20, value=5)
        offset_treino = st.number_input("Offset para treinamentos", min_value=0, value=0)
        
        # Botão para atualizar
        if st.button("Atualizar Histórico de Treinamentos"):
            with st.spinner("Carregando dados..."):
                treinamentos = fazer_requisicao("/treinamentos", params={"limit": limit_treino, "offset": offset_treino})
                
                if treinamentos:
                    if len(treinamentos) == 0:
                        st.info("Nenhum treinamento encontrado.")
                    else:
                        # Converte para DataFrame para melhor visualização
                        df_treinamentos = []
                        for t in treinamentos:
                            df_treinamentos.append({
                                "ID": t["id"],
                                "Data": datetime.fromisoformat(t["timestamp"]).strftime("%d/%m/%Y %H:%M"),
                                "Amostras": t["num_amostras"],
                                "R²": f"{t['r2_score']:.4f}",
                                "RMSE": f"{t.get('rmse', 'N/A'):.2f}" if t.get('rmse') is not None else "N/A",
                                "MAE": f"{t.get('mae', 'N/A'):.2f}" if t.get('mae') is not None else "N/A",
                            })
                        
                        df = pd.DataFrame(df_treinamentos)
                        st.write(df)
                        
                        # Se houver treinamentos, permite selecionar um para detalhes
                        if treinamentos:
                            selected_id = st.selectbox(
                                "Selecione um treinamento para ver detalhes",
                                options=[t["id"] for t in treinamentos],
                                format_func=lambda x: f"Treinamento #{x} - {[t for t in treinamentos if t['id'] == x][0]['timestamp'][:10]}"
                            )
                            
                            # Opção para incluir amostras
                            include_samples = st.checkbox("Incluir dados de treinamento")
                            
                            if st.button("Ver Detalhes"):
                                with st.spinner("Carregando detalhes..."):
                                    treinamento = fazer_requisicao(
                                        f"/treinamentos/{selected_id}", 
                                        params={"include_samples": include_samples}
                                    )
                                    
                                    if treinamento:
                                        st.subheader(f"Detalhes do Treinamento #{treinamento['id']}")
                                        
                                        # Informações gerais
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("R² Score", f"{treinamento['r2_score']:.4f}")
                                        
                                        if treinamento.get('rmse') is not None:
                                            col2.metric("RMSE", f"{treinamento['rmse']:.2f}")
                                        
                                        if treinamento.get('mae') is not None:
                                            col3.metric("MAE", f"{treinamento['mae']:.2f}")
                                        
                                        # Coeficientes
                                        if "coeficientes" in treinamento:
                                            st.subheader("Coeficientes")
                                            
                                            coefs = treinamento["coeficientes"]
                                            coef_df = pd.DataFrame({
                                                "Feature": list(coefs.keys()),
                                                "Coeficiente": list(coefs.values())
                                            })
                                            
                                            fig = px.bar(
                                                coef_df, 
                                                x="Feature", 
                                                y="Coeficiente",
                                                title="Coeficientes do Modelo",
                                                color="Coeficiente",
                                                color_continuous_scale="RdBu",
                                                height=400
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Dados de treinamento
                                        if include_samples and "dados_treinamento" in treinamento:
                                            st.subheader("Dados de Treinamento")
                                            
                                            # Converte para DataFrame
                                            amostras = treinamento["dados_treinamento"]
                                            df_amostras = pd.DataFrame(amostras)
                                            
                                            # Exibe tabela
                                            st.write(df_amostras)
                                            
                                            # Scatter plot de área x preço
                                            fig = px.scatter(
                                                df_amostras,
                                                x="area",
                                                y="preco",
                                                title="Relação entre Área e Preço",
                                                labels={"area": "Área (m²)", "preco": "Preço (R$)"},
                                                color_discrete_sequence=["royalblue"],
                                                height=400
                                            )
                                            st.plotly_chart(fig, use_container_width=True)


# Interface principal
def main():
    """Função principal da aplicação"""
    # Inicializa o estado da sessão
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Sidebar para navegação
    with st.sidebar:
        st.title("Navegação")
        
        # Menu de navegação
        st.radio(
            "Escolha uma página:",
            options=["Home", "Prever", "Treinar", "Histórico"],
            key="navigation",
            on_change=lambda: setattr(st.session_state, "page", st.session_state.navigation.lower())
        )
        
        # Informações adicionais
        st.markdown("---")
        st.markdown("### Sobre")
        st.markdown("API de Preços de Imóveis v7.0")
        st.markdown("Desenvolvido com Streamlit e FastAPI")
        st.markdown("© 2023")
    
    # Renderiza a página selecionada
    if st.session_state.page == "home":
        pagina_inicial()
    elif st.session_state.page == "prever":
        pagina_previsao()
    elif st.session_state.page == "treinar":
        pagina_treinamento()
    elif st.session_state.page == "histórico":
        pagina_historico()


if __name__ == "__main__":
    main() 