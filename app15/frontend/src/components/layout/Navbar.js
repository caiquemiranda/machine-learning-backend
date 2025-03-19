import React from 'react';
import { Navbar as BootstrapNavbar, Nav, Container, NavDropdown } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Navbar = () => {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <BootstrapNavbar bg="primary" variant="dark" expand="lg">
            <Container>
                <BootstrapNavbar.Brand as={Link} to="/">
                    Sistema de Previsões ML
                </BootstrapNavbar.Brand>
                <BootstrapNavbar.Toggle aria-controls="basic-navbar-nav" />
                <BootstrapNavbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto">
                        {isAuthenticated && (
                            <>
                                <Nav.Link as={Link} to="/dashboard">Dashboard</Nav.Link>
                                <Nav.Link as={Link} to="/predictions/new">Nova Previsão</Nav.Link>
                                <Nav.Link as={Link} to="/predictions/history">Histórico</Nav.Link>
                                {user?.is_admin && (
                                    <Nav.Link as={Link} to="/admin">Admin</Nav.Link>
                                )}
                            </>
                        )}
                    </Nav>

                    <Nav>
                        {isAuthenticated ? (
                            <NavDropdown title={user?.username || 'Usuário'} id="user-dropdown">
                                <NavDropdown.Item as={Link} to="/profile">
                                    Meu Perfil
                                </NavDropdown.Item>
                                <NavDropdown.Divider />
                                <NavDropdown.Item onClick={handleLogout}>
                                    Sair
                                </NavDropdown.Item>
                            </NavDropdown>
                        ) : (
                            <>
                                <Nav.Link as={Link} to="/login">Login</Nav.Link>
                                <Nav.Link as={Link} to="/register">Registrar</Nav.Link>
                            </>
                        )}
                    </Nav>
                </BootstrapNavbar.Collapse>
            </Container>
        </BootstrapNavbar>
    );
};

export default Navbar; 