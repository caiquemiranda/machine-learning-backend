import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import jwtDecode from 'jwt-decode';

// Criação do contexto de autenticação
export const AuthContext = createContext();

// Hook para usar o contexto de autenticação
export const useAuth = () => useContext(AuthContext);

// Provider do contexto de autenticação
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Ao iniciar, verifica se há um token salvo
    useEffect(() => {
        const checkToken = async () => {
            try {
                const token = localStorage.getItem('token');
                if (token) {
                    // Verificar se o token é válido
                    const decodedToken = jwtDecode(token);
                    const currentTime = Date.now() / 1000;

                    if (decodedToken.exp < currentTime) {
                        // Token expirado, fazer logout
                        handleLogout();
                    } else {
                        // Token válido, buscar informações do usuário
                        setAxiosAuthHeader(token);
                        const response = await axios.get('/api/users/me');
                        setUser(response.data);
                    }
                }
            } catch (error) {
                console.error('Erro ao verificar autenticação:', error);
                handleLogout();
            } finally {
                setLoading(false);
            }
        };

        checkToken();
    }, []);

    // Configurar cabeçalho de autenticação para requisições Axios
    const setAxiosAuthHeader = (token) => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        } else {
            delete axios.defaults.headers.common['Authorization'];
        }
    };

    // Função para fazer login
    const handleLogin = async (username, password) => {
        try {
            setError(null);

            // Formatando os dados para envio como form data
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            // Requisição de login
            const response = await axios.post('/api/token', formData);
            const { access_token } = response.data;

            // Salvar token no localStorage
            localStorage.setItem('token', access_token);

            // Configurar cabeçalho de autenticação
            setAxiosAuthHeader(access_token);

            // Buscar informações do usuário
            const userResponse = await axios.get('/api/users/me');
            setUser(userResponse.data);

            return true;
        } catch (error) {
            console.error('Erro ao fazer login:', error);
            setError(error.response?.data?.detail || 'Erro ao fazer login. Tente novamente.');
            return false;
        }
    };

    // Função para fazer logout
    const handleLogout = () => {
        // Remover token do localStorage
        localStorage.removeItem('token');

        // Remover cabeçalho de autenticação
        setAxiosAuthHeader(null);

        // Limpar estado do usuário
        setUser(null);
    };

    // Função para registrar um novo usuário
    const handleRegister = async (userData) => {
        try {
            setError(null);

            // Requisição de registro
            const response = await axios.post('/api/users', userData);

            // Fazer login automaticamente após o registro
            return await handleLogin(userData.username, userData.password);
        } catch (error) {
            console.error('Erro ao registrar:', error);
            setError(error.response?.data?.detail || 'Erro ao registrar. Tente novamente.');
            return false;
        }
    };

    // Valores do contexto
    const value = {
        user,
        loading,
        error,
        setError,
        login: handleLogin,
        logout: handleLogout,
        register: handleRegister,
        isAuthenticated: !!user
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 