import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserService, PredictionService } from '../services/api';
import { FaChartLine, FaHistory, FaPlus, FaUser } from 'react-icons/fa';

const Dashboard = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState(null);
    const [recentPredictions, setRecentPredictions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Buscar estatísticas do usuário
                const statsData = await UserService.getStats();
                setStats(statsData);

                // Buscar previsões recentes
                const predictionsData = await PredictionService.getAll();
                setRecentPredictions(predictionsData.slice(0, 5)); // Apenas as 5 previsões mais recentes
            } catch (err) {
                console.error('Erro ao carregar dados do dashboard:', err);
                setError('Falha ao carregar os dados do dashboard. Por favor, tente novamente.');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    const formatDate = (dateString) => {
        const options = { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('pt-BR', options);
    };

    return (
        <div>
            <h2 className="page-title">Dashboard</h2>

            {error && <Alert variant="danger">{error}</Alert>}

            {!loading && stats && (
                <>
                    <Row className="mb-4">
                        <Col md={12}>
                            <Card className="mb-4">
                                <Card.Body>
                                    <Card.Title>Bem-vindo, {user?.full_name || user?.username}!</Card.Title>
                                    <Card.Text>
                                        Este é o sistema de previsões com machine learning. Faça previsões, visualize seu histórico e treine modelos personalizados.
                                    </Card.Text>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>

                    <Row className="mb-4">
                        <Col md={6} lg={3} className="mb-3">
                            <Card className="stats-card h-100">
                                <Card.Body>
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <Card.Title className="mb-0">{stats.prediction_count}</Card.Title>
                                            <Card.Text className="text-muted">Previsões Realizadas</Card.Text>
                                        </div>
                                        <FaChartLine size={30} className="text-primary" />
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={6} lg={3} className="mb-3">
                            <Card className="stats-card h-100">
                                <Card.Body>
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <Card.Title className="mb-0">{stats.log_count}</Card.Title>
                                            <Card.Text className="text-muted">Logs de Atividade</Card.Text>
                                        </div>
                                        <FaHistory size={30} className="text-primary" />
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={6} lg={3} className="mb-3">
                            <Card className="stats-card h-100">
                                <Card.Body>
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <Card.Title className="mb-0">{stats.account_age_days}</Card.Title>
                                            <Card.Text className="text-muted">Dias de Conta</Card.Text>
                                        </div>
                                        <FaUser size={30} className="text-primary" />
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>

                        {user?.is_admin && stats.total_users && (
                            <Col md={6} lg={3} className="mb-3">
                                <Card className="stats-card admin-card h-100">
                                    <Card.Body>
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div>
                                                <Card.Title className="mb-0">{stats.total_users}</Card.Title>
                                                <Card.Text className="text-muted">Usuários Totais</Card.Text>
                                            </div>
                                            <FaUser size={30} className="text-danger" />
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        )}
                    </Row>

                    <Row className="mb-4">
                        <Col md={12}>
                            <Card>
                                <Card.Header className="d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0">Previsões Recentes</h5>
                                    <Link to="/predictions/history">
                                        <Button variant="outline-primary" size="sm">Ver Todas</Button>
                                    </Link>
                                </Card.Header>
                                <Card.Body>
                                    {recentPredictions.length > 0 ? (
                                        <div className="table-responsive">
                                            <table className="table table-hover history-table mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>ID</th>
                                                        <th>Tipo</th>
                                                        <th>Resultado</th>
                                                        <th>Data</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {recentPredictions.map((prediction) => (
                                                        <tr key={prediction.id}>
                                                            <td>{prediction.id}</td>
                                                            <td>{prediction.prediction_type === 'classifier' ? 'Classificação' : 'Regressão'}</td>
                                                            <td>
                                                                {prediction.prediction_type === 'classifier'
                                                                    ? `Classe: ${prediction.output_data.class}`
                                                                    : `Valor: ${prediction.output_data.value.toFixed(2)}`}
                                                            </td>
                                                            <td>{formatDate(prediction.created_at)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    ) : (
                                        <p className="text-center mb-0">Nenhuma previsão realizada ainda.</p>
                                    )}
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>

                    <Row>
                        <Col md={12} className="text-center">
                            <Link to="/predictions/new">
                                <Button variant="primary" size="lg">
                                    <FaPlus className="me-2" /> Nova Previsão
                                </Button>
                            </Link>
                        </Col>
                    </Row>
                </>
            )}
        </div>
    );
};

export default Dashboard; 