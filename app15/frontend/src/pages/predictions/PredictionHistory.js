import React, { useState, useEffect } from 'react';
import { Card, Table, Alert, Button, Badge, Spinner } from 'react-bootstrap';
import { PredictionService } from '../../services/api';
import { FaSearch, FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';

const PredictionHistory = () => {
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortField, setSortField] = useState('created_at');
    const [sortDirection, setSortDirection] = useState('desc');

    useEffect(() => {
        const fetchPredictions = async () => {
            try {
                setLoading(true);
                setError(null);

                const data = await PredictionService.getAll();
                setPredictions(data);
            } catch (err) {
                console.error('Erro ao buscar previsões:', err);
                setError('Falha ao carregar o histórico de previsões. Por favor, tente novamente.');
            } finally {
                setLoading(false);
            }
        };

        fetchPredictions();
    }, []);

    const handleSort = (field) => {
        if (field === sortField) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    const getSortIcon = (field) => {
        if (field !== sortField) return <FaSort />;
        return sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />;
    };

    const sortedPredictions = [...predictions].sort((a, b) => {
        let aValue = a[sortField];
        let bValue = b[sortField];

        // Tratamento especial para datas
        if (sortField === 'created_at') {
            aValue = new Date(aValue).getTime();
            bValue = new Date(bValue).getTime();
        }

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    const formatDate = (dateString) => {
        const options = { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('pt-BR', options);
    };

    const renderPredictionResult = (prediction) => {
        const { prediction_type, output_data } = prediction;

        if (prediction_type === 'classifier') {
            return `Classe: ${output_data.class}`;
        } else {
            return `Valor: ${output_data.value.toFixed(2)}`;
        }
    };

    return (
        <div>
            <h2 className="page-title">Histórico de Previsões</h2>

            {error && <Alert variant="danger">{error}</Alert>}

            <Card>
                <Card.Body>
                    {loading ? (
                        <div className="text-center p-4">
                            <Spinner animation="border" role="status">
                                <span className="visually-hidden">Carregando...</span>
                            </Spinner>
                            <p className="mt-2">Carregando histórico...</p>
                        </div>
                    ) : (
                        <>
                            {predictions.length === 0 ? (
                                <Alert variant="info">
                                    Você ainda não realizou nenhuma previsão.
                                    <Button
                                        variant="link"
                                        href="/predictions/new"
                                        className="p-0 ms-2"
                                    >
                                        Fazer uma previsão agora
                                    </Button>
                                </Alert>
                            ) : (
                                <div className="table-responsive">
                                    <Table striped hover className="history-table">
                                        <thead>
                                            <tr>
                                                <th onClick={() => handleSort('id')} style={{ cursor: 'pointer' }}>
                                                    ID {getSortIcon('id')}
                                                </th>
                                                <th onClick={() => handleSort('prediction_type')} style={{ cursor: 'pointer' }}>
                                                    Tipo {getSortIcon('prediction_type')}
                                                </th>
                                                <th>Entrada</th>
                                                <th>Resultado</th>
                                                <th onClick={() => handleSort('created_at')} style={{ cursor: 'pointer' }}>
                                                    Data {getSortIcon('created_at')}
                                                </th>
                                                <th>Ações</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sortedPredictions.map((prediction) => (
                                                <tr key={prediction.id}>
                                                    <td>{prediction.id}</td>
                                                    <td>
                                                        <Badge bg={prediction.prediction_type === 'classifier' ? 'primary' : 'success'}>
                                                            {prediction.prediction_type === 'classifier' ? 'Classificação' : 'Regressão'}
                                                        </Badge>
                                                    </td>
                                                    <td>
                                                        <small>
                                                            {Object.entries(prediction.input_data).map(([key, value], index) => (
                                                                <div key={index}>
                                                                    <strong>{key}:</strong> {value}
                                                                </div>
                                                            ))}
                                                        </small>
                                                    </td>
                                                    <td>{renderPredictionResult(prediction)}</td>
                                                    <td>{formatDate(prediction.created_at)}</td>
                                                    <td>
                                                        <Button
                                                            variant="outline-secondary"
                                                            size="sm"
                                                            title="Ver detalhes"
                                                        >
                                                            <FaSearch />
                                                        </Button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </div>
                            )}
                        </>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default PredictionHistory; 