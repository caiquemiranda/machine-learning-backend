import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Spinner, Alert, ProgressBar, Button } from 'react-bootstrap';
import axios from 'axios';
import { FaSmile, FaFrown, FaSync } from 'react-icons/fa';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FeedbackHistory = () => {
    const [feedbacks, setFeedbacks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchFeedbacks = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/feedbacks`);
            setFeedbacks(response.data);
            setError(null);
        } catch (err) {
            console.error('Erro ao buscar feedbacks:', err);
            setError('Não foi possível carregar o histórico de feedbacks.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFeedbacks();
        // Atualizar a cada 10 segundos
        const interval = setInterval(fetchFeedbacks, 10000);
        return () => clearInterval(interval);
    }, []);

    const formatConfidence = (confidence) => {
        return `${(confidence * 100).toFixed(0)}%`;
    };

    const truncateText = (text, maxLength = 100) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    };

    return (
        <Card className="shadow-sm">
            <Card.Body>
                <div className="d-flex justify-content-between align-items-center mb-3">
                    <Card.Title>Histórico de Feedbacks</Card.Title>
                    <Button
                        variant="outline-secondary"
                        size="sm"
                        onClick={fetchFeedbacks}
                        disabled={loading}
                    >
                        <FaSync className={loading ? 'spinner' : ''} /> Atualizar
                    </Button>
                </div>

                {loading && feedbacks.length === 0 ? (
                    <div className="text-center my-4">
                        <Spinner animation="border" variant="primary" />
                        <p className="mt-2">Carregando histórico...</p>
                    </div>
                ) : error ? (
                    <Alert variant="danger">{error}</Alert>
                ) : feedbacks.length === 0 ? (
                    <Alert variant="info">
                        Nenhum feedback classificado ainda. Use o formulário para enviar seu primeiro feedback.
                    </Alert>
                ) : (
                    <div className="table-responsive">
                        <Table hover className="feedback-table">
                            <thead>
                                <tr>
                                    <th>Texto</th>
                                    <th>Sentimento</th>
                                    <th>Confiança</th>
                                </tr>
                            </thead>
                            <tbody>
                                {feedbacks.map((feedback) => (
                                    <tr key={feedback.id} className="feedback-entry">
                                        <td className="text-truncate-container">{truncateText(feedback.text)}</td>
                                        <td>
                                            <Badge
                                                bg={feedback.is_positive ? 'success' : 'danger'}
                                                className="d-flex align-items-center"
                                            >
                                                {feedback.is_positive ?
                                                    <><FaSmile className="me-1" /> Positivo</> :
                                                    <><FaFrown className="me-1" /> Negativo</>
                                                }
                                            </Badge>
                                        </td>
                                        <td style={{ width: '15%' }}>
                                            <div className="d-flex flex-column">
                                                <small>{formatConfidence(feedback.confidence)}</small>
                                                <ProgressBar
                                                    variant={feedback.is_positive ? "success" : "danger"}
                                                    now={feedback.confidence * 100}
                                                    className="confidence-progress mt-1"
                                                />
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </div>
                )}
            </Card.Body>
        </Card>
    );
};

export default FeedbackHistory; 