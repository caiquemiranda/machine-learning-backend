import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

def generate_sample_data(n_samples=1000):
    """Gerar dados sintéticos para treinamento do modelo."""
    np.random.seed(42)
    
    # Gerar features aleatórias
    area = np.random.uniform(500, 5000, n_samples)
    bedrooms = np.random.randint(1, 6, n_samples)
    bathrooms = np.random.randint(1, 4, n_samples)
    stories = np.random.randint(1, 4, n_samples)
    parking = np.random.randint(0, 3, n_samples)
    age = np.random.uniform(1, 30, n_samples)
    
    # Criar preço baseado nas features com algum ruído
    # Coeficientes de importância
    price = (
        area * 100 +
        bedrooms * 20000 +
        bathrooms * 15000 +
        stories * 10000 +
        parking * 5000 -
        age * 1000 +
        np.random.normal(0, 20000, n_samples)
    )
    
    # Criar DataFrame
    data = pd.DataFrame({
        'area': area,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'stories': stories,
        'parking': parking,
        'age': age,
        'price': price
    })
    
    return data

def train_and_save_model():
    """Treinar e salvar o modelo de regressão linear."""
    print("Gerando dados de treinamento...")
    data = generate_sample_data()
    
    # Separar features e target
    X = data.drop('price', axis=1)
    y = data['price']
    
    # Dividir em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Treinar o modelo
    print("Treinando modelo de regressão linear...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Avaliar o modelo
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Performance do modelo - MSE: {mse:.2f}, R²: {r2:.4f}")
    
    # Salvar o modelo
    joblib.dump(model, "model.joblib")
    print("Modelo salvo com sucesso!")
    
    return model

if __name__ == "__main__":
    train_and_save_model() 