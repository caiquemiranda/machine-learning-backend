import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
});

// Funções para interagir com a API
export const makePrediction = async (data) => {
    try {
        const response = await api.post('/predict', data);
        return response.data;
    } catch (error) {
        console.error('Erro ao fazer predição:', error);
        throw error;
    }
};

export const trainModel = async (modelConfig) => {
    try {
        const response = await api.post('/train', modelConfig);
        return response.data;
    } catch (error) {
        console.error('Erro ao treinar modelo:', error);
        throw error;
    }
};

export const getCurrentMetrics = async () => {
    try {
        const response = await api.get('/metrics/current');
        return response.data;
    } catch (error) {
        console.error('Erro ao obter métricas atuais:', error);
        throw error;
    }
};

export const getMetricsHistory = async (limit = 10) => {
    try {
        const response = await api.get(`/metrics?limit=${limit}`);
        return response.data;
    } catch (error) {
        console.error('Erro ao obter histórico de métricas:', error);
        throw error;
    }
};

export const getPredictionLogs = async (limit = 50) => {
    try {
        const response = await api.get(`/logs?limit=${limit}`);
        return response.data;
    } catch (error) {
        console.error('Erro ao obter histórico de predições:', error);
        throw error;
    }
};

export const getConfusionMatrix = async () => {
    try {
        const response = await api.get('/visualizations/confusion-matrix');
        return response.data;
    } catch (error) {
        console.error('Erro ao obter matriz de confusão:', error);
        throw error;
    }
};

export const getFeatureImportance = async () => {
    try {
        const response = await api.get('/visualizations/feature-importance');
        return response.data;
    } catch (error) {
        console.error('Erro ao obter importância das features:', error);
        throw error;
    }
};

export const getModelConfig = async () => {
    try {
        const response = await api.get('/model/config');
        return response.data;
    } catch (error) {
        console.error('Erro ao obter configuração do modelo:', error);
        throw error;
    }
};

export default api; 