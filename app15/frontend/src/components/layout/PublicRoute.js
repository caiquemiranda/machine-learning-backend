import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Navbar from './Navbar';
import { Container, Spinner } from 'react-bootstrap';

// Componente para rotas públicas (redireciona usuários autenticados se necessário)
const PublicRoute = ({ restricted = false }) => {
  const { isAuthenticated, loading } = useAuth();

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

  // Se é uma rota restrita (como login) e o usuário está autenticado, redireciona para dashboard
  if (restricted && isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }

  // Renderiza o conteúdo
  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
};

export default PublicRoute; 