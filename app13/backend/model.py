import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Constantes
MODEL_DIR = "models"
CURRENT_MODEL_PATH = os.path.join(MODEL_DIR, "current_model.joblib")
MODEL_CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
METRICS_PLOT_DIR = "plots"

# Garantir que os diretórios existam
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(METRICS_PLOT_DIR, exist_ok=True)

# Configuração padrão do modelo
DEFAULT_CONFIG = {
    "model_type": "random_forest",
    "version": 1,
    "parameters": {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    }
}

def generate_synthetic_data(n_samples=500):
    """
    Gera dados sintéticos para diagnóstico médico simulado.
    
    Features:
    - Idade
    - Pressão Arterial (sistólica)
    - Nível de Glicose
    - Frequência Cardíaca
    - Índice de Massa Corporal (IMC)
    - Quantidade de exercício semanal (horas)
    - Fumante (0/1)
    
    Diagnóstico: 
    - "saudavel"
    - "risco_baixo"
    - "risco_moderado"
    - "risco_alto"
    """
    np.random.seed(42)
    
    # Gerar features aleatórias
    age = np.random.randint(18, 90, n_samples)
    blood_pressure = np.random.randint(90, 180, n_samples)
    glucose = np.random.randint(70, 200, n_samples)
    heart_rate = np.random.randint(50, 120, n_samples)
    bmi = np.random.uniform(18, 40, n_samples)
    exercise_hours = np.random.uniform(0, 15, n_samples)
    smoker = np.random.randint(0, 2, n_samples)
    
    # Criar regras básicas para classificação
    risk_score = (
        (age > 60) * 2 +
        (blood_pressure > 140) * 3 +
        (glucose > 125) * 3 +
        (heart_rate > 100) * 2 +
        (bmi > 30) * 2 +
        (exercise_hours < 2) * 1 +
        (smoker == 1) * 3
    )
    
    diagnosis = []
    for score in risk_score:
        if score <= 2:
            diagnosis.append("saudavel")
        elif score <= 5:
            diagnosis.append("risco_baixo")
        elif score <= 9:
            diagnosis.append("risco_moderado")
        else:
            diagnosis.append("risco_alto")
    
    # Criar DataFrame
    data = pd.DataFrame({
        'idade': age,
        'pressao_arterial': blood_pressure,
        'glicose': glucose,
        'freq_cardiaca': heart_rate,
        'imc': bmi,
        'exercicio_semanal': exercise_hours,
        'fumante': smoker,
        'diagnostico': diagnosis
    })
    
    return data

def load_model_config():
    """Carrega a configuração do modelo atual."""
    if os.path.exists(MODEL_CONFIG_PATH):
        with open(MODEL_CONFIG_PATH, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_model_config(config):
    """Salva a configuração do modelo."""
    with open(MODEL_CONFIG_PATH, 'w') as f:
        json.dump(config, f)

def create_model(config=None):
    """Cria uma instância do modelo com base na configuração."""
    if config is None:
        config = load_model_config()
    
    model_type = config["model_type"]
    params = config["parameters"]
    
    if model_type == "random_forest":
        return RandomForestClassifier(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", None),
            random_state=params.get("random_state", 42)
        )
    elif model_type == "logistic_regression":
        return LogisticRegression(
            C=params.get("C", 1.0),
            max_iter=params.get("max_iter", 1000),
            random_state=params.get("random_state", 42)
        )
    else:
        raise ValueError(f"Tipo de modelo não suportado: {model_type}")

def load_or_train_model(force_retrain=False, custom_data=None):
    """
    Carrega o modelo existente ou treina um novo se necessário.
    
    Args:
        force_retrain: Se True, treina um novo modelo mesmo se já existir
        custom_data: Dados personalizados para treino, se disponíveis
    
    Returns:
        model: Modelo treinado
        X_test: Dados de teste
        y_test: Rótulos de teste
        metrics: Métricas de avaliação
    """
    config = load_model_config()
    
    # Verificar se modelo já existe e não é forçado retreino
    if os.path.exists(CURRENT_MODEL_PATH) and not force_retrain:
        model = joblib.load(CURRENT_MODEL_PATH)
        
        # Gerar alguns dados de teste para uso em predições de exemplo
        data = custom_data if custom_data is not None else generate_synthetic_data(100)
        X = data.drop('diagnostico', axis=1)
        y = data['diagnostico']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        return model, X_test, y_test, None
    
    # Treinar novo modelo
    data = custom_data if custom_data is not None else generate_synthetic_data(1000)
    
    # Separar features e target
    X = data.drop('diagnostico', axis=1)
    y = data['diagnostico']
    
    # Dividir em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Criar e treinar o modelo
    model = create_model(config)
    model.fit(X_train, y_train)
    
    # Salvar o modelo treinado
    joblib.dump(model, CURRENT_MODEL_PATH)
    
    # Calcular métricas
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average='weighted')),
        "recall": float(recall_score(y_test, y_pred, average='weighted')),
        "f1_score": float(f1_score(y_test, y_pred, average='weighted')),
        "dataset_size": len(data),
        "model_name": config['model_type'],
        "version": config['version']
    }
    
    # Incrementar a versão
    config['version'] += 1
    save_model_config(config)
    
    return model, X_test, y_test, metrics

def predict(features):
    """
    Realiza predição usando o modelo carregado.
    
    Args:
        features: Dicionário com os valores das features
        
    Returns:
        result: Dicionário com a predição e probabilidades
    """
    # Carregar o modelo
    if not os.path.exists(CURRENT_MODEL_PATH):
        model, _, _, _ = load_or_train_model()
    else:
        model = joblib.load(CURRENT_MODEL_PATH)
    
    # Preparar os dados para predição
    data = pd.DataFrame([features])
    
    # Fazer a predição
    prediction = model.predict(data)[0]
    
    # Obter as probabilidades
    probabilities = model.predict_proba(data)[0]
    
    # Mapear classes e probabilidades
    classes = model.classes_
    probs_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
    
    return {
        "prediction": prediction,
        "prediction_probability": float(max(probabilities)),
        "all_probabilities": probs_dict,
        "model_version": load_model_config()["version"] - 1
    }

def generate_confusion_matrix(y_true, y_pred, classes=None):
    """
    Gera matriz de confusão como imagem codificada em base64.
    
    Args:
        y_true: Valores reais
        y_pred: Valores preditos
        classes: Lista de classes
    
    Returns:
        base64_image: String codificada em base64 da imagem
    """
    cm = confusion_matrix(y_true, y_pred)
    if classes is None:
        classes = sorted(set(y_true))
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predição')
    plt.ylabel('Valor Real')
    plt.title('Matriz de Confusão')
    
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Codificar em base64
    base64_image = base64.b64encode(buf.read()).decode('utf-8')
    return base64_image

def generate_feature_importance(model, feature_names):
    """
    Gera gráfico de importância de features como imagem codificada em base64.
    
    Args:
        model: Modelo treinado (deve ter atributo feature_importances_)
        feature_names: Lista com nomes das features
    
    Returns:
        base64_image: String codificada em base64 da imagem
    """
    if not hasattr(model, 'feature_importances_'):
        return None
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.title('Importância das Features')
    plt.bar(range(len(importances)), importances[indices], align='center')
    plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=90)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Codificar em base64
    base64_image = base64.b64encode(buf.read()).decode('utf-8')
    return base64_image 