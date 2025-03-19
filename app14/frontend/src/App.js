import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Nav, Navbar } from 'react-bootstrap';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import EstimadorForm from './components/EstimadorForm';
import EstimativasList from './components/EstimativasList';
import TiposSolicitacao from './components/TiposSolicitacao';
import ModelInfo from './components/ModelInfo';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
    const [modeloInfo, setModeloInfo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Verificar informações do modelo ao carregar
        const fetchModeloInfo = async () => {
            try {
                const response = await fetch(`${API_URL}/modelo-info/`);
                const data = await response.json();
                setModeloInfo(data);
            } catch (error) {
                console.error('Erro ao obter informações do modelo:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchModeloInfo();
    }, []);

    return (
        <Router>
            <div className="App">
                <Navbar bg="primary" variant="dark" expand="lg">
                    <Container>
                        <Navbar.Brand as={Link} to="/">Estimador de Tempo de Atendimento</Navbar.Brand>
                        <Navbar.Toggle aria-controls="basic-navbar-nav" />
                        <Navbar.Collapse id="basic-navbar-nav">
                            <Nav className="ms-auto">
                                <Nav.Link as={Link} to="/">Nova Estimativa</Nav.Link>
                                <Nav.Link as={Link} to="/estimativas">Histórico</Nav.Link>
                                <Nav.Link as={Link} to="/tipos">Tipos de Solicitação</Nav.Link>
                                <Nav.Link as={Link} to="/modelo">Informações do Modelo</Nav.Link>
                            </Nav>
                        </Navbar.Collapse>
                    </Container>
                </Navbar>

                <Container className="mt-4 mb-5">
                    {loading ? (
                        <div className="text-center mt-5">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">Carregando...</span>
                            </div>
                            <p className="mt-2">Carregando aplicação...</p>
                        </div>
                    ) : (
                        <Routes>
                            <Route
                                path="/"
                                element={
                                    <EstimadorForm
                                        apiUrl={API_URL}
                                        modeloTreinado={modeloInfo?.status === 'treinado'}
                                    />
                                }
                            />
                            <Route
                                path="/estimativas"
                                element={<EstimativasList apiUrl={API_URL} />}
                            />
                            <Route
                                path="/tipos"
                                element={<TiposSolicitacao apiUrl={API_URL} />}
                            />
                            <Route
                                path="/modelo"
                                element={<ModelInfo apiUrl={API_URL} modeloInfo={modeloInfo} />}
                            />
                        </Routes>
                    )}
                </Container>

                <footer className="bg-light py-4 mt-5 border-top">
                    <Container>
                        <Row>
                            <Col className="text-center">
                                <p className="mb-0">Estimador de Tempo de Atendimento &copy; {new Date().getFullYear()}</p>
                                <p className="text-muted small mb-0">Um sistema para previsão de tempo de atendimento utilizando Machine Learning</p>
                            </Col>
                        </Row>
                    </Container>
                </footer>
            </div>
        </Router>
    );
}

export default App; 