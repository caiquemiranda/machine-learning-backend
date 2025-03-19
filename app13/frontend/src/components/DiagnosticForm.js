import React, { useState } from 'react';
import { Form, Button, Card, Row, Col, ProgressBar, Alert } from 'react-bootstrap';
import { FaHeartbeat, FaTint, FaWeight, FaRunning, FaSmoking } from 'react-icons/fa';
import { makePrediction } from '../api';

const DiagnosticForm = () => {
    const [formData, setFormData] = useState({
        idade: 40,
        pressao_arterial: 120,
        glicose: 100,
        freq_cardiaca: 70,
        imc: 25,
        exercicio_semanal: 3,
        fumante: 0
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: name === 'fumante' ? parseInt(value) : parseFloat(value)
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const result = await makePrediction(formData);
            setResult(result);
        } catch (err) {
            console.error('Erro ao fazer diagnóstico:', err);
            setError('Ocorreu um erro ao processar o diagnóstico. Por favor, tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    // Função para formatar valores percentuais
    const formatPercent = (value) => {
        return (value * 100).toFixed(1) + '%';
    };

    // Função para determinar a classe de cor conforme o diagnóstico
    const getDiagnosticClass = (prediction) => {
        switch (prediction) {
            case 'saudavel':
                return 'saudavel';
            case 'risco_baixo':
                return 'risco_baixo';
            case 'risco_moderado':
                return 'risco_moderado';
            case 'risco_alto':
                return 'risco_alto';
            default:
                return '';
        }
    };

    // Função para obter o rótulo do diagnóstico em português
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

    return (
        <div>
            <h2 className="mb-4">Diagnóstico Preditivo</h2>

            <Row>
                <Col lg={6}>
                    <Card className="dashboard-card">
                        <Card.Body>
                            <Card.Title>Informações do Paciente</Card.Title>
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Idade</Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="idade"
                                        value={formData.idade}
                                        onChange={handleChange}
                                        min="0"
                                        max="120"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        <FaTint className="me-1 text-danger" /> Pressão Arterial (sistólica)
                                    </Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="pressao_arterial"
                                        value={formData.pressao_arterial}
                                        onChange={handleChange}
                                        min="70"
                                        max="250"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Nível de Glicose</Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="glicose"
                                        value={formData.glicose}
                                        onChange={handleChange}
                                        min="50"
                                        max="500"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        <FaHeartbeat className="me-1 text-danger" /> Frequência Cardíaca (bpm)
                                    </Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="freq_cardiaca"
                                        value={formData.freq_cardiaca}
                                        onChange={handleChange}
                                        min="40"
                                        max="200"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        <FaWeight className="me-1" /> IMC (Índice de Massa Corporal)
                                    </Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="imc"
                                        value={formData.imc}
                                        onChange={handleChange}
                                        min="10"
                                        max="60"
                                        step="0.1"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        <FaRunning className="me-1 text-success" /> Exercício Semanal (horas)
                                    </Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="exercicio_semanal"
                                        value={formData.exercicio_semanal}
                                        onChange={handleChange}
                                        min="0"
                                        max="40"
                                        step="0.5"
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        <FaSmoking className="me-1 text-secondary" /> Fumante
                                    </Form.Label>
                                    <Form.Select
                                        name="fumante"
                                        value={formData.fumante}
                                        onChange={handleChange}
                                        required
                                    >
                                        <option value="0">Não</option>
                                        <option value="1">Sim</option>
                                    </Form.Select>
                                </Form.Group>

                                <Button variant="primary" type="submit" disabled={loading}>
                                    {loading ? 'Processando...' : 'Realizar Diagnóstico'}
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col lg={6}>
                    {error && (
                        <Alert variant="danger">{error}</Alert>
                    )}

                    {result && (
                        <div className={`prediction-result ${getDiagnosticClass(result.prediction)}`}>
                            <div className="prediction-title">
                                <h4>Resultado do Diagnóstico</h4>
                                <span className={`prediction-tag ${getDiagnosticClass(result.prediction)}`}>
                                    {getDiagnosticLabel(result.prediction)}
                                </span>
                            </div>

                            <p className="mt-3">
                                <strong>Confiança:</strong> {formatPercent(result.prediction_probability)}
                            </p>

                            <ProgressBar
                                variant={getDiagnosticClass(result.prediction)}
                                now={result.prediction_probability * 100}
                                className="confidence-bar"
                            />

                            <hr />

                            <h5>Probabilidades por Categoria</h5>
                            <Row className="mt-3">
                                {Object.entries(result.all_probabilities).map(([category, probability]) => (
                                    <Col sm={6} key={category} className="mb-2">
                                        <div className="d-flex justify-content-between mb-1">
                                            <span>{getDiagnosticLabel(category)}</span>
                                            <span>{formatPercent(probability)}</span>
                                        </div>
                                        <ProgressBar
                                            variant={getDiagnosticClass(category)}
                                            now={probability * 100}
                                            className="confidence-bar"
                                        />
                                    </Col>
                                ))}
                            </Row>

                            <div className="mt-4 text-muted">
                                <small>Modelo versão {result.model_version}</small>
                            </div>
                        </div>
                    )}

                    {!result && !error && (
                        <Card className="dashboard-card h-100 d-flex align-items-center justify-content-center">
                            <Card.Body className="text-center">
                                <FaHeartbeat className="text-primary mb-3" style={{ fontSize: '3rem' }} />
                                <h4>Preencha o formulário</h4>
                                <p className="text-muted">
                                    Complete o formulário ao lado e clique em "Realizar Diagnóstico" para obter uma previsão.
                                </p>
                            </Card.Body>
                        </Card>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default DiagnosticForm; 