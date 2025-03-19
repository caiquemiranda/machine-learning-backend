import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaStethoscope, FaCog, FaHistory, FaChartBar } from 'react-icons/fa';

const NavigationBar = () => {
    const location = useLocation();

    return (
        <Navbar bg="dark" variant="dark" expand="lg" sticky="top">
            <Container>
                <Navbar.Brand as={Link} to="/">Sistema de Diagnóstico Preditivo</Navbar.Brand>
                <Navbar.Toggle aria-controls="basic-navbar-nav" />
                <Navbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto">
                        <Nav.Link
                            as={Link}
                            to="/dashboard"
                            active={location.pathname === '/dashboard'}
                        >
                            <FaHome className="me-1" /> Dashboard
                        </Nav.Link>
                        <Nav.Link
                            as={Link}
                            to="/diagnostic"
                            active={location.pathname === '/diagnostic'}
                        >
                            <FaStethoscope className="me-1" /> Diagnóstico
                        </Nav.Link>
                        <Nav.Link
                            as={Link}
                            to="/training"
                            active={location.pathname === '/training'}
                        >
                            <FaCog className="me-1" /> Treinar Modelo
                        </Nav.Link>
                        <Nav.Link
                            as={Link}
                            to="/history"
                            active={location.pathname === '/history'}
                        >
                            <FaHistory className="me-1" /> Histórico
                        </Nav.Link>
                        <Nav.Link
                            as={Link}
                            to="/visualizations"
                            active={location.pathname === '/visualizations'}
                        >
                            <FaChartBar className="me-1" /> Visualizações
                        </Nav.Link>
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
};

export default NavigationBar; 