import React, { useState } from 'react';
import { Form, Button, Card, Alert } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PredictionForm = () => {
    const [formData, setFormData] = useState({
        area: 1000,
        bedrooms: 2,
        bathrooms: 1,
        stories: 1,
        parking: 1,
        age: 5
    });

    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: Number(value)
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post(`${API_URL}/predict`, formData);
            setPrediction(response.data.predicted_price);
        } catch (err) {
            console.error('Erro ao fazer a previsão:', err);
            setError('Erro ao fazer a previsão. Tente novamente mais tarde.');
        } finally {
            setLoading(false);
        }
    };

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
                <Card.Title>Preencha os dados da casa</Card.Title>
                <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-3">
                        <Form.Label>Área (m²)</Form.Label>
                        <Form.Control
                            type="number"
                            name="area"
                            value={formData.area}
                            onChange={handleChange}
                            min="10"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Quartos</Form.Label>
                        <Form.Control
                            type="number"
                            name="bedrooms"
                            value={formData.bedrooms}
                            onChange={handleChange}
                            min="1"
                            max="10"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Banheiros</Form.Label>
                        <Form.Control
                            type="number"
                            name="bathrooms"
                            value={formData.bathrooms}
                            onChange={handleChange}
                            min="1"
                            max="5"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Andares</Form.Label>
                        <Form.Control
                            type="number"
                            name="stories"
                            value={formData.stories}
                            onChange={handleChange}
                            min="1"
                            max="4"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Vagas de Estacionamento</Form.Label>
                        <Form.Control
                            type="number"
                            name="parking"
                            value={formData.parking}
                            onChange={handleChange}
                            min="0"
                            max="5"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Idade (anos)</Form.Label>
                        <Form.Control
                            type="number"
                            name="age"
                            value={formData.age}
                            onChange={handleChange}
                            min="0"
                            max="100"
                            required
                        />
                    </Form.Group>

                    <Button variant="primary" type="submit" disabled={loading}>
                        {loading ? 'Calculando...' : 'Prever Preço'}
                    </Button>
                </Form>

                {error && (
                    <Alert variant="danger" className="mt-3">
                        {error}
                    </Alert>
                )}

                {prediction && (
                    <div className="prediction-result mt-3">
                        <h4>Preço Estimado</h4>
                        <p className="display-4">{formatPrice(prediction)}</p>
                        <p className="text-muted">
                            Este valor é baseado nas características informadas e no modelo de regressão linear.
                        </p>
                    </div>
                )}
            </Card.Body>
        </Card>
    );
};

export default PredictionForm; 