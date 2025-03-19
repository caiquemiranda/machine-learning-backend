import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Alert, Spinner, Button } from 'react-bootstrap';
import { FaSync } from 'react-icons/fa';
import { getPredictionLogs } from '../api';

const PredictionHistory = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const data = await getPredictionLogs(50);
            setLogs(data);
            setError(null);
        } catch (err) {
            console.error('Erro ao buscar logs de predição:', err);
            setError('Não foi possível carregar o histórico de predições. Verifique se o servidor está em execução.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const getDiagnosticLabel = (prediction) => {
        switch (prediction) {
            case 'saudavel':
                return 'Saudável';
            case 'risco_baixo':
                return 'Risco Baixo';
            case 'risco_moderado':
                return 'Risco Moderado';
            case 'risco_alto':
                return 'Risco Alto';
            default:
                return prediction;
        }
    };

    const getBadgeVariant = (prediction) => {
        switch (prediction) {
            case 'saudavel':
                return 'success';
            case 'risco_baixo':
                return 'warning';
            case 'risco_moderado':
                return 'orange';
            case 'risco_alto':
                return 'danger';
            default:
                return 'secondary';
        }
    };

    const formatPercent = (value) => {
        return (value * 100).toFixed(1) + '%';
    };

    if (loading && logs.length === 0) {
        return (
            <div className="loading-spinner">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Histórico de Diagnósticos</h2>
                <Button
                    variant="outline-primary"
                    onClick={fetchLogs}
                    disabled={loading}
                    className="d-flex align-items-center"
                >
                    <FaSync className={loading ? 'me-2 spinner' : 'me-2'} />
                    Atualizar
                </Button>
            </div>

            {error && (
                <Alert variant="danger">
                    {error}
                </Alert>
            )}

            {!error && logs.length === 0 ? (
                <Alert variant="info">
                    Nenhum diagnóstico foi realizado ainda. Use a página de Diagnóstico para fazer sua primeira predição.
                </Alert>
            ) : (
                <Card className="dashboard-card">
                    <Card.Body>
                        <div className="table-responsive">
                            <Table hover>
                                <thead>
                                    <tr>
                                        <th>Data/Hora</th>
                                        <th>Diagnóstico</th>
                                        <th>Confiança</th>
                                        <th>Versão do Modelo</th>
                                        <th>Detalhes do Paciente</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log) => (
                                        <tr key={log.id}>
                                            <td>{formatDate(log.timestamp)}</td>
                                            <td>
                                                <Badge
                                                    bg={getBadgeVariant(log.prediction)}
                                                    className="d-inline-block px-3 py-2"
                                                >
                                                    {getDiagnosticLabel(log.prediction)}
                                                </Badge>
                                            </td>
                                            <td>{formatPercent(log.prediction_probability)}</td>
                                            <td>v{log.model_version}</td>
                                            <td>
                                                <details>
                                                    <summary>Ver detalhes</summary>
                                                    <div className="mt-2">
                                                        <ul className="list-unstyled">
                                                            <li><strong>Idade:</strong> {log.input_data.idade} anos</li>
                                                            <li><strong>Pressão Arterial:</strong> {log.input_data.pressao_arterial} mmHg</li>
                                                            <li><strong>Glicose:</strong> {log.input_data.glicose} mg/dL</li>
                                                            <li><strong>Freq. Cardíaca:</strong> {log.input_data.freq_cardiaca} bpm</li>
                                                            <li><strong>IMC:</strong> {log.input_data.imc}</li>
                                                            <li><strong>Exercício Semanal:</strong> {log.input_data.exercicio_semanal} h</li>
                                                            <li><strong>Fumante:</strong> {log.input_data.fumante ? 'Sim' : 'Não'}</li>
                                                        </ul>
                                                    </div>
                                                </details>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </div>
                    </Card.Body>
                </Card>
            )}
        </div>
    );
};

export default PredictionHistory; 