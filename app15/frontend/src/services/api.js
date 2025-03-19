import axios from 'axios';

// Configuração base do Axios
axios.defaults.baseURL = process.env.REACT_APP_API_URL || '';

// Serviço de previsões
export const PredictionService = {
    // Obter todas as previsões do usuário
    getAll: async () => {
        try {
            const response = await axios.get('/api/predictions');
            return response.data;
        } catch (error) {
            console.error('Erro ao buscar previsões:', error);
            throw error;
        }
    },

    // Criar uma nova previsão
    create: async (predictionData) => {
        try {
            const response = await axios.post('/api/predictions', predictionData);
            return response.data;
        } catch (error) {
            console.error('Erro ao criar previsão:', error);
            throw error;
        }
    }
};

// Serviço de modelos
export const ModelService = {
    // Treinar um modelo
    train: async (trainingData) => {
        try {
            const response = await axios.post('/api/models/train', trainingData);
            return response.data;
        } catch (error) {
            console.error('Erro ao treinar modelo:', error);
            throw error;
        }
    },

    // Obter métricas de um modelo
    getMetrics: async (modelType, modelName) => {
        try {
            const response = await axios.get(`/api/models/${modelType}/${modelName}/metrics`);
            return response.data;
        } catch (error) {
            console.error('Erro ao obter métricas do modelo:', error);
            throw error;
        }
    }
};

// Serviço de usuários
export const UserService = {
    // Atualizar perfil do usuário
    updateProfile: async (userData) => {
        try {
            const response = await axios.put('/api/users/me', userData);
            return response.data;
        } catch (error) {
            console.error('Erro ao atualizar perfil:', error);
            throw error;
        }
    },

    // Obter estatísticas do usuário
    getStats: async () => {
        try {
            const response = await axios.get('/api/stats');
            return response.data;
        } catch (error) {
            console.error('Erro ao obter estatísticas:', error);
            throw error;
        }
    }
};

// Serviço de logs
export const LogService = {
    // Obter logs do usuário
    getLogs: async () => {
        try {
            const response = await axios.get('/api/logs');
            return response.data;
        } catch (error) {
            console.error('Erro ao buscar logs:', error);
            throw error;
        }
    }
};

// Serviço de administração (para usuários admin)
export const AdminService = {
    // Obter todos os usuários
    getAllUsers: async () => {
        try {
            const response = await axios.get('/api/admin/users');
            return response.data;
        } catch (error) {
            console.error('Erro ao buscar usuários:', error);
            throw error;
        }
    },

    // Obter todos os logs
    getAllLogs: async () => {
        try {
            const response = await axios.get('/api/admin/logs');
            return response.data;
        } catch (error) {
            console.error('Erro ao buscar logs:', error);
            throw error;
        }
    }
}; 