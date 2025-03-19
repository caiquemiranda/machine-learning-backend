import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { getCurrentMetrics, getMetricsHistory } from '../api';

// Registrar componentes do Chart.js
Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const Dashboard = () => {
    const [currentMetrics, setCurrentMetrics] = useState(null);
    const [metricsHistory, setMetricsHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [current, history] = await Promise.all([
                    getCurrentMetrics(),
                    getMetricsHistory(10)
                ]);

                setCurrentMetrics(current);
                setMetricsHistory(history.reverse()); // Inverter para mostrar evolução cronológica
                setError(null);
            } catch (err) {
                console.error('Erro ao carregar dados do dashboard:', err);
                setError('Não foi possível carregar os dados do dashboard. Verifique se o servidor está em execução.');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const formatValue = (value) => {
        return (value * 100).toFixed(2) + '%';
    };

    const prepareChartData = () => {
        if (!metricsHistory.length) return null;

        const labels = metricsHistory.map(m => `Versão ${m.version}`);

        return {
            labels,
            datasets: [
                {
                    label: 'Acurácia',
                    data: metricsHistory.map(m => m.accuracy),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    tension: 0.2
                },
                {
                    label: 'Precisão',
                    data: metricsHistory.map(m => m.precision),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    tension: 0.2
                },
                {
                    label: 'Recall',
                    data: metricsHistory.map(m => m.recall),
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    tension: 0.2
                },
                {
                    label: 'F1 Score',
                    data: metricsHistory.map(m => m.f1_score),
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.5)',
                    tension: 0.2
                }
            ]
        };
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Evolução das Métricas do Modelo'
            },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const label = context.dataset.label || '';
                        const value = context.parsed.y;
                        return `${label}: ${formatValue(value)}`;
                    }
                }
            }
        },
        scales: {
            y: {
                min: 0,
                max: 1,
                ticks: {
                    callback: function (value) {
                        return formatValue(value);
                    }
                }
            }
        }
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="danger">
                {error}
            </Alert>
        );
    }

    return (
        <div>
            <h2 className="mb-4">Dashboard</h2>

            {currentMetrics && (
                <>
                    <Row>
                        <Col md={3}>
                            <Card className="dashboard-card">
                                <Card.Body className="metric-card">
                                    <div className="metric-title">Acurácia</div>
                                    <div className="metric-value">{formatValue(currentMetrics.accuracy)}</div>
                                    <div className="version-tag">Versão {currentMetrics.version}</div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={3}>
                            <Card className="dashboard-card">
                                <Card.Body className="metric-card">
                                    <div className="metric-title">Precisão</div>
                                    <div className="metric-value">{formatValue(currentMetrics.precision)}</div>
                                    <div className="version-tag">Versão {currentMetrics.version}</div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={3}>
                            <Card className="dashboard-card">
                                <Card.Body className="metric-card">
                                    <div className="metric-title">Recall</div>
                                    <div className="metric-value">{formatValue(currentMetrics.recall)}</div>
                                    <div className="version-tag">Versão {currentMetrics.version}</div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={3}>
                            <Card className="dashboard-card">
                                <Card.Body className="metric-card">
                                    <div className="metric-title">F1 Score</div>
                                    <div className="metric-value">{formatValue(currentMetrics.f1_score)}</div>
                                    <div className="version-tag">Versão {currentMetrics.version}</div>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>

                    <Row className="mt-4">
                        <Col md={8}>
                            <Card className="dashboard-card">
                                <Card.Body>
                                    <Card.Title>Evolução das Métricas</Card.Title>
                                    <div className="chart-container">
                                        {metricsHistory.length > 0 ? (
                                            <Line data={prepareChartData()} options={chartOptions} />
                                        ) : (
                                            <Alert variant="info">Não há histórico de métricas suficiente para gerar o gráfico.</Alert>
                                        )}
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>

                        <Col md={4}>
                            <Card className="dashboard-card">
                                <Card.Body>
                                    <Card.Title>Informações do Modelo</Card.Title>
                                    <ul className="list-group mt-3">
                                        <li className="list-group-item d-flex justify-content-between align-items-center">
                                            Tipo de Modelo
                                            <span className="badge bg-primary rounded-pill">{currentMetrics.model_name}</span>
                                        </li>
                                        <li className="list-group-item d-flex justify-content-between align-items-center">
                                            Versão
                                            <span className="badge bg-secondary rounded-pill">{currentMetrics.version}</span>
                                        </li>
                                        <li className="list-group-item d-flex justify-content-between align-items-center">
                                            Tamanho do Dataset
                                            <span className="badge bg-info rounded-pill">{currentMetrics.dataset_size} registros</span>
                                        </li>
                                        <li className="list-group-item d-flex justify-content-between align-items-center">
                                            Data de Treinamento
                                            <span className="badge bg-light text-dark rounded-pill">
                                                {new Date(currentMetrics.training_date).toLocaleString()}
                                            </span>
                                        </li>
                                    </ul>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </>
            )}
        </div>
    );
};

export default Dashboard; 