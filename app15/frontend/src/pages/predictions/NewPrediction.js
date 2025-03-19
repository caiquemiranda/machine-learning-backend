import React, { useState } from 'react';
import { Card, Form, Button, Alert, Spinner, Row, Col, Tab, Nav } from 'react-bootstrap';
import { PredictionService } from '../../services/api';

const NewPrediction = () => {
    const [predictionType, setPredictionType] = useState('classifier');
    const [formValues, setFormValues] = useState({
        feature1: '',
        feature2: ''
    });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormValues({
            ...formValues,
            [name]: value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            setLoading(true);
            setError(null);
            setResult(null);

            // Converter valores de string para número se necessário
            const inputData = {};
            Object.keys(formValues).forEach(key => {
                const value = formValues[key].trim();
                if (value === '') return;

                // Tentar converter para número se possível
                const numValue = Number(value);
                inputData[key] = isNaN(numValue) ? value : numValue;
            });

            // Verificar se há dados suficientes
            if (Object.keys(inputData).length < 2) {
                throw new Error('Por favor, forneça pelo menos dois valores de entrada para a previsão.');
            }

            // Fazer a requisição de previsão
            const response = await PredictionService.create({
                prediction_type: predictionType,
                input_data: inputData
            });

            // Definir resultado
            setResult(response);

        } catch (err) {
            console.error('Erro ao fazer previsão:', err);
            setError(err.message || 'Ocorreu um erro ao processar a previsão. Por favor, tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    const renderClassifierResult = () => {
        if (!result || !result.output_data) return null;

        const { class: predictedClass, probabilities, class_names } = result.output_data;

        return (
            <div>
                <p><strong>Classe Prevista:</strong> {predictedClass}</p>

                {probabilities && class_names && (
                    <div>
                        <p><strong>Probabilidades:</strong></p>
                        <ul>
                            {class_names.map((className, index) => (
                                <li key={index}>
                                    {className}: {(probabilities[index] * 100).toFixed(2)}%
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        );
    };

    const renderRegressorResult = () => {
        if (!result || !result.output_data) return null;

        const { value } = result.output_data;

        return (
            <div>
                <p><strong>Valor Previsto:</strong> {value.toFixed(4)}</p>
            </div>
        );
    };

    return (
        <div>
            <h2 className="page-title">Nova Previsão</h2>

            <Row>
                <Col md={8} lg={6} className="mx-auto">
                    <Card className="mb-4">
                        <Card.Header>
                            <h5 className="mb-0">Formulário de Previsão</h5>
                        </Card.Header>
                        <Card.Body>
                            {error && <Alert variant="danger">{error}</Alert>}

                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tipo de Previsão</Form.Label>
                                    <Form.Select
                                        value={predictionType}
                                        onChange={(e) => setPredictionType(e.target.value)}
                                    >
                                        <option value="classifier">Classificação</option>
                                        <option value="regressor">Regressão</option>
                                    </Form.Select>
                                    <Form.Text className="text-muted">
                                        {predictionType === 'classifier'
                                            ? 'Classificação prevê categorias ou classes.'
                                            : 'Regressão prevê valores numéricos contínuos.'}
                                    </Form.Text>
                                </Form.Group>

                                <div className="mb-3">
                                    <Form.Label>Dados de Entrada</Form.Label>
                                    <Tab.Container defaultActiveKey="tab-features">
                                        <Nav variant="tabs" className="mb-3">
                                            <Nav.Item>
                                                <Nav.Link eventKey="tab-features">Features</Nav.Link>
                                            </Nav.Item>
                                        </Nav>
                                        <Tab.Content>
                                            <Tab.Pane eventKey="tab-features">
                                                <Row>
                                                    <Col md={6}>
                                                        <Form.Group className="mb-3">
                                                            <Form.Label>Feature 1</Form.Label>
                                                            <Form.Control
                                                                type="text"
                                                                name="feature1"
                                                                value={formValues.feature1}
                                                                onChange={handleInputChange}
                                                                placeholder="Valor numérico"
                                                            />
                                                        </Form.Group>
                                                    </Col>
                                                    <Col md={6}>
                                                        <Form.Group className="mb-3">
                                                            <Form.Label>Feature 2</Form.Label>
                                                            <Form.Control
                                                                type="text"
                                                                name="feature2"
                                                                value={formValues.feature2}
                                                                onChange={handleInputChange}
                                                                placeholder="Valor numérico"
                                                            />
                                                        </Form.Group>
                                                    </Col>
                                                </Row>
                                            </Tab.Pane>
                                        </Tab.Content>
                                    </Tab.Container>
                                </div>

                                <div className="d-grid">
                                    <Button
                                        variant="primary"
                                        type="submit"
                                        disabled={loading}
                                    >
                                        {loading ? (
                                            <>
                                                <Spinner
                                                    as="span"
                                                    animation="border"
                                                    size="sm"
                                                    role="status"
                                                    aria-hidden="true"
                                                    className="me-2"
                                                />
                                                Processando...
                                            </>
                                        ) : (
                                            'Fazer Previsão'
                                        )}
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>

                    {result && (
                        <Card className="prediction-card fade-in">
                            <Card.Header className="bg-success text-white">
                                <h5 className="mb-0">Resultado da Previsão</h5>
                            </Card.Header>
                            <Card.Body>
                                {predictionType === 'classifier'
                                    ? renderClassifierResult()
                                    : renderRegressorResult()}

                                <hr />

                                <div className="text-muted">
                                    <small>ID da Previsão: {result.id}</small>
                                    <br />
                                    <small>Data: {new Date(result.created_at).toLocaleString('pt-BR')}</small>
                                </div>
                            </Card.Body>
                        </Card>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default NewPrediction; 