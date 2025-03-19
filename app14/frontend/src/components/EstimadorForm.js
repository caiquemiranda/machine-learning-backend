import React, { useState, useEffect } from 'react';
import { Form, Button, Card, Row, Col, Alert, Badge } from 'react-bootstrap';
import { FaClock, FaSave, FaCalculator } from 'react-icons/fa';

const EstimadorForm = ({ apiUrl, modeloTreinado }) => {
    const [tiposSolicitacao, setTiposSolicitacao] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [estimativaResult, setEstimativaResult] = useState(null);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({
        tipo_solicitacao_id: '',
        complexidade: 3,
        tempo_real: '',
        observacoes: ''
    });

    // Buscar tipos de solicitação ao carregar o componente
    useEffect(() => {
        const fetchTiposSolicitacao = async () => {
            try {
                const response = await fetch(`${apiUrl}/tipos-solicitacao/`);
                if (!response.ok) {
                    throw new Error(`Erro ao carregar tipos de solicitação: ${response.statusText}`);
                }
                const data = await response.json();
                setTiposSolicitacao(data);
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        };

        fetchTiposSolicitacao();
    }, [apiUrl]);

    // Manipulador de mudanças no formulário
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    // Obter estimativa sem salvar
    const handlePredict = async (e) => {
        e.preventDefault();
        if (!formData.tipo_solicitacao_id) {
            setError('Por favor, selecione um tipo de solicitação');
            return;
        }

        try {
            setSubmitting(true);
            setError(null);

            const response = await fetch(`${apiUrl}/predict/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tipo_solicitacao_id: parseInt(formData.tipo_solicitacao_id),
                    complexidade: parseInt(formData.complexidade)
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao realizar estimativa');
            }

            const data = await response.json();
            setEstimativaResult(data);
        } catch (error) {
            setError(error.message);
        } finally {
            setSubmitting(false);
        }
    };

    // Salvar estimativa no banco de dados
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.tipo_solicitacao_id) {
            setError('Por favor, selecione um tipo de solicitação');
            return;
        }

        try {
            setSubmitting(true);
            setError(null);

            const requestData = {
                tipo_solicitacao_id: parseInt(formData.tipo_solicitacao_id),
                complexidade: parseInt(formData.complexidade)
            };

            // Adicionar tempo_real e observacoes apenas se tiverem sido preenchidos
            if (formData.tempo_real) {
                requestData.tempo_real = parseFloat(formData.tempo_real);
            }

            if (formData.observacoes) {
                requestData.observacoes = formData.observacoes;
            }

            const response = await fetch(`${apiUrl}/estimativas/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao salvar estimativa');
            }

            const data = await response.json();
            setEstimativaResult({
                tipo_solicitacao: tiposSolicitacao.find(t => t.id === data.tipo_solicitacao_id)?.nome || 'Desconhecido',
                complexidade: data.complexidade,
                tempo_estimado: data.tempo_estimado
            });

            // Limpar o formulário após o envio bem-sucedido
            setFormData({
                tipo_solicitacao_id: '',
                complexidade: 3,
                tempo_real: '',
                observacoes: ''
            });
        } catch (error) {
            setError(error.message);
        } finally {
            setSubmitting(false);
        }
    };

    // Renderizar badge de complexidade com cores diferentes
    const renderComplexityBadge = (complexity) => {
        let variant;
        switch (complexity) {
            case 1:
                variant = 'success';
                break;
            case 2:
                variant = 'info';
                break;
            case 3:
                variant = 'warning';
                break;
            case 4:
                variant = 'orange';
                break;
            case 5:
                variant = 'danger';
                break;
            default:
                variant = 'secondary';
        }
        return <Badge bg={variant}>{complexity}</Badge>;
    };

    if (loading) {
        return <div className="text-center mt-4">Carregando...</div>;
    }

    return (
        <div>
            <h1 className="mb-4 text-center">Estimador de Tempo de Atendimento</h1>

            {!modeloTreinado && (
                <Alert variant="warning">
                    <Alert.Heading>Modelo não treinado</Alert.Heading>
                    <p>
                        O modelo de machine learning ainda não foi treinado. As estimativas podem não ser precisas.
                        Acesse a página "Informações do Modelo" para treinar o modelo.
                    </p>
                </Alert>
            )}

            {error && <Alert variant="danger">{error}</Alert>}

            <Row>
                <Col md={6}>
                    <Card className="mb-4">
                        <Card.Header>Formulário de Estimativa</Card.Header>
                        <Card.Body>
                            <Form>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tipo de Solicitação</Form.Label>
                                    <Form.Select
                                        name="tipo_solicitacao_id"
                                        value={formData.tipo_solicitacao_id}
                                        onChange={handleChange}
                                        required
                                    >
                                        <option value="">Selecione um tipo de solicitação</option>
                                        {tiposSolicitacao.map((tipo) => (
                                            <option key={tipo.id} value={tipo.id}>
                                                {tipo.nome}
                                            </option>
                                        ))}
                                    </Form.Select>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Complexidade (1-5)</Form.Label>
                                    <div className="d-flex align-items-center">
                                        <Form.Range
                                            name="complexidade"
                                            min="1"
                                            max="5"
                                            step="1"
                                            value={formData.complexidade}
                                            onChange={handleChange}
                                        />
                                        <span className="ms-2 badge bg-primary">{formData.complexidade}</span>
                                    </div>
                                    <div className="mt-1 d-flex justify-content-between">
                                        <small className="text-muted">Simples</small>
                                        <small className="text-muted">Complexo</small>
                                    </div>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Tempo Real (opcional, em minutos)</Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="tempo_real"
                                        value={formData.tempo_real}
                                        onChange={handleChange}
                                        placeholder="Tempo real de atendimento (se conhecido)"
                                    />
                                    <Form.Text className="text-muted">
                                        Informe o tempo real se quiser usar esse registro para treinar o modelo no futuro.
                                    </Form.Text>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Observações</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        name="observacoes"
                                        value={formData.observacoes}
                                        onChange={handleChange}
                                        placeholder="Observações sobre a solicitação (opcional)"
                                    />
                                </Form.Group>

                                <div className="d-flex justify-content-between">
                                    <Button
                                        variant="primary"
                                        onClick={handlePredict}
                                        disabled={submitting || !formData.tipo_solicitacao_id}
                                    >
                                        <FaCalculator className="me-2" />
                                        Estimar Tempo
                                    </Button>
                                    <Button
                                        variant="success"
                                        onClick={handleSubmit}
                                        disabled={submitting || !formData.tipo_solicitacao_id}
                                    >
                                        <FaSave className="me-2" />
                                        Salvar Estimativa
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={6}>
                    {estimativaResult && (
                        <Card className="result-card">
                            <Card.Header>Resultado da Estimativa</Card.Header>
                            <Card.Body>
                                <div className="text-center mb-4">
                                    <FaClock size={48} className="text-primary mb-3" />
                                    <h2 className="mb-0 tempo-estimado">
                                        {estimativaResult.tempo_estimado.toFixed(1)} minutos
                                    </h2>
                                    <p className="text-muted mt-1">Tempo estimado de atendimento</p>
                                </div>

                                <Card.Text>
                                    <strong>Tipo de Solicitação:</strong> {estimativaResult.tipo_solicitacao}
                                </Card.Text>
                                <Card.Text>
                                    <strong>Complexidade:</strong> {renderComplexityBadge(estimativaResult.complexidade)}
                                </Card.Text>
                                <Card.Text className="text-muted small">
                                    Esta estimativa foi gerada usando um modelo de machine learning baseado em dados históricos.
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default EstimadorForm; 