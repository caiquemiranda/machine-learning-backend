import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Navbar from './Navbar';
import { Container, Spinner } from 'react-bootstrap';

// Componente para rotas que exigem autenticação
const PrivateRoute = ({ requireAdmin = false }) => {
    const { isAuthenticated, loading, user } = useAuth();

    // Se ainda está carregando, exibe um spinner
    if (loading) {
        return (
            <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Carregando...</span>
                </Spinner>
            </Container>
        );
    }

    // Se não está autenticado, redireciona para login
    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    // Se requer admin e o usuário não é admin, redireciona para dashboard
    if (requireAdmin && !user?.is_admin) {
        return <Navigate to="/dashboard" />;
    }

    // Se autenticado e atende aos requisitos, renderiza o conteúdo
    return (
        <>
            <Navbar />
            <Container className="py-4">
                <Outlet />
            </Container>
        </>
    );
};

export default PrivateRoute; 