import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import joblib
import os

def download_nltk_resources():
    """Baixar recursos do NLTK necessários para o processamento de texto."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

def preprocess_text(text):
    """Função para pré-processar texto."""
    # Converter para minúsculas
    text = text.lower()
    # Remover caracteres especiais
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Tokenização
    tokens = word_tokenize(text)
    # Remover stopwords
    stop_words = set(stopwords.words('portuguese'))
    tokens = [word for word in tokens if word not in stop_words]
    # Juntar tokens novamente em uma string
    return ' '.join(tokens)

def generate_sample_data(n_samples=1000):
    """Gerar dados sintéticos para treinamento do modelo."""
    np.random.seed(42)
    
    # Lista de palavras positivas e negativas em português
    positive_words = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'fantástico', 'incrível', 'adorei', 
                     'gostei', 'satisfeito', 'feliz', 'recomendo', 'perfeito', 'melhor']
    
    negative_words = ['ruim', 'péssimo', 'terrível', 'horrível', 'decepcionante', 'insatisfeito', 
                      'desapontado', 'frustrado', 'pior', 'negativo', 'não recomendo', 'odiei']
    
    # Frases base para cada classe
    positive_templates = [
        "Eu {adv} {verbo} o produto. É muito {adj}.",
        "O serviço foi {adj} e o atendimento {adj}.",
        "{adv} {verbo} a experiência. {adj}!",
        "A qualidade é {adv} {adj}. {verbo} comprar novamente.",
        "Produto {adj}, {verbo} o resultado."
    ]
    
    negative_templates = [
        "Eu {adv} {verbo} o produto. É muito {adj}.",
        "O serviço foi {adj} e o atendimento {adj}.",
        "{adv} {verbo} a experiência. {adj}!",
        "A qualidade é {adv} {adj}. Não {verbo} comprar novamente.",
        "Produto {adj}, não {verbo} o resultado."
    ]
    
    positive_verbs = ['gostei', 'adorei', 'amei', 'recomendo', 'apreciei']
    negative_verbs = ['detestei', 'odiei', 'não gostei', 'não recomendo', 'desaprovei']
    
    positive_adverbs = ['muito', 'extremamente', 'realmente', 'bastante', 'super']
    negative_adverbs = ['pouco', 'nada', 'mal', 'minimamente', 'insuficientemente']
    
    data = []
    labels = []
    
    # Gerar exemplos positivos
    for _ in range(n_samples // 2):
        template = np.random.choice(positive_templates)
        adj = np.random.choice(positive_words)
        verbo = np.random.choice(positive_verbs)
        adv = np.random.choice(positive_adverbs)
        
        text = template.format(adj=adj, verbo=verbo, adv=adv)
        data.append(text)
        labels.append(1)  # 1 para positivo
    
    # Gerar exemplos negativos
    for _ in range(n_samples // 2):
        template = np.random.choice(negative_templates)
        adj = np.random.choice(negative_words)
        verbo = np.random.choice(negative_verbs)
        adv = np.random.choice(negative_adverbs)
        
        text = template.format(adj=adj, verbo=verbo, adv=adv)
        data.append(text)
        labels.append(0)  # 0 para negativo
    
    # Criar DataFrame
    df = pd.DataFrame({
        'text': data,
        'is_positive': labels
    })
    
    # Embaralhar os dados
    df = df.sample(frac=1).reset_index(drop=True)
    
    return df

def train_and_save_model():
    """Treinar e salvar o modelo de classificação de sentimentos."""
    # Baixar recursos do NLTK
    download_nltk_resources()
    
    print("Gerando dados de treinamento...")
    data = generate_sample_data()
    
    # Pré-processar os textos
    data['processed_text'] = data['text'].apply(preprocess_text)
    
    # Separar features e target
    X = data['processed_text']
    y = data['is_positive']
    
    # Dividir em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Criar pipeline com vetorização TF-IDF e classificação com Regressão Logística
    print("Treinando modelo de classificação...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000)),
        ('classifier', LogisticRegression(random_state=42))
    ])
    
    # Treinar o modelo
    pipeline.fit(X_train, y_train)
    
    # Avaliar o modelo
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Acurácia do modelo: {accuracy:.4f}")
    print("Relatório de classificação:")
    print(classification_report(y_test, y_pred, target_names=['Negativo', 'Positivo']))
    
    # Salvar o modelo
    joblib.dump(pipeline, "model.joblib")
    print("Modelo salvo com sucesso!")
    
    return pipeline

if __name__ == "__main__":
    train_and_save_model() 