import React, { useState, useEffect } from 'react';
import { Card, Table, Alert, Spinner } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PredictionHistory = () => {
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPredictions = async () => {
            try {
                const response = await axios.get(`${API_URL}/predictions`);
                setPredictions(response.data);
            } catch (err) {
                console.error('Erro ao buscar previsões:', err);
                setError('Não foi possível carregar o histórico de previsões.');
            } finally {
                setLoading(false);
            }
        };

        fetchPredictions();
        // Atualizar a cada 5 segundos
        const interval = setInterval(fetchPredictions, 5000);
        return () => clearInterval(interval);
    }, []);

    const formatPrice = (price) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2
        }).format(price);
    };

    return (
        <Card className="shadow-sm">
            <Card.Body>
                <Card.Title>Histórico de Previsões</Card.Title>

                {loading ? (
                    <div className="text-center my-4">
                        <Spinner animation="border" variant="primary" />
                        <p className="mt-2">Carregando histórico...</p>
                    </div>
                ) : error ? (
                    <Alert variant="danger">{error}</Alert>
                ) : predictions.length === 0 ? (
                    <Alert variant="info">
                        Nenhuma previsão realizada ainda. Utilize o formulário para fazer sua primeira previsão.
                    </Alert>
                ) : (
                    <div className="table-responsive">
                        <Table hover>
                            <thead>
                                <tr>
                                    <th>Área (m²)</th>
                                    <th>Quartos</th>
                                    <th>Banheiros</th>
                                    <th>Andares</th>
                                    <th>Estac.</th>
                                    <th>Idade</th>
                                    <th>Preço Estimado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {predictions.map((prediction) => (
                                    <tr key={prediction.id}>
                                        <td>{prediction.area}</td>
                                        <td>{prediction.bedrooms}</td>
                                        <td>{prediction.bathrooms}</td>
                                        <td>{prediction.stories}</td>
                                        <td>{prediction.parking}</td>
                                        <td>{prediction.age}</td>
                                        <td className="fw-bold text-success">
                                            {formatPrice(prediction.predicted_price)}
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

export default PredictionHistory; 