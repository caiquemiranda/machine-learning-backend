import React, { useState, useEffect } from 'react';
import { Form, Button, Card, Alert, Spinner, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { trainModel, getModelConfig } from '../api';

const ModelTraining = () => {
    const navigate = useNavigate();

    const [modelType, setModelType] = useState('random_forest');
    const [parameters, setParameters] = useState({
        random_forest: {
            n_estimators: 100,
            max_depth: 10,
            random_state: 42
        },
        logistic_regression: {
            C: 1.0,
            max_iter: 1000,
            random_state: 42
        }
    });

    const [currentParams, setCurrentParams] = useState({});
    const [loading, setLoading] = useState(false);
    const [configLoading, setConfigLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // Carregar configuração atual do modelo ao montar o componente
    useEffect(() => {
        const loadModelConfig = async () => {
            try {
                setConfigLoading(true);
                const config = await getModelConfig();

                setModelType(config.model_type);

                // Atualizar parâmetros com os valores da configuração
                setParameters(prevParams => ({
                    ...prevParams,
                    [config.model_type]: config.parameters
                }));

                setCurrentParams(config.parameters);
            } catch (err) {
                console.error('Erro ao carregar configuração do modelo:', err);
                setError('Não foi possível carregar a configuração atual do modelo.');
            } finally {
                setConfigLoading(false);
            }
        };

        loadModelConfig();
    }, []);

    // Atualizar os parâmetros quando o tipo de modelo muda
    useEffect(() => {
        setCurrentParams(parameters[modelType]);
    }, [modelType, parameters]);

    const handleModelTypeChange = (e) => {
        setModelType(e.target.value);
    };

    const handleParameterChange = (paramName, value) => {
        // Converter para número se o valor for numérico
        const numValue = !isNaN(value) ? parseFloat(value) : value;

        setParameters(prevParams => ({
            ...prevParams,
            [modelType]: {
                ...prevParams[modelType],
                [paramName]: numValue
            }
        }));

        setCurrentParams(prevParams => ({
            ...prevParams,
            [paramName]: numValue
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const modelConfig = {
                model_type: modelType,
                parameters: currentParams
            };

            await trainModel(modelConfig);
            setSuccess('Modelo treinado com sucesso! As novas métricas estão disponíveis no dashboard.');

            // Redirecionar para o dashboard após 3 segundos
            setTimeout(() => {
                navigate('/dashboard');
            }, 3000);
        } catch (err) {
            console.error('Erro ao treinar modelo:', err);
            setError('Ocorreu um erro ao treinar o modelo. Por favor, tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    // Renderizar parâmetros específicos do tipo de modelo selecionado
    const renderParameters = () => {
        if (modelType === 'random_forest') {
            return (
                <>
                    <Form.Group className="mb-3">
                        <Form.Label>Número de Estimadores (n_estimators)</Form.Label>
                        <Form.Control
                            type="number"
                            value={currentParams.n_estimators || 100}
                            onChange={(e) => handleParameterChange('n_estimators', parseInt(e.target.value))}
                            min="10"
                            max="500"
                        />
                        <Form.Text className="text-muted">
                            Número de árvores na floresta. Valores entre 10 e 500.
                        </Form.Text>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Profundidade Máxima (max_depth)</Form.Label>
                        <Form.Control
                            type="number"
                            value={currentParams.max_depth || 10}
                            onChange={(e) => handleParameterChange('max_depth', parseInt(e.target.value))}
                            min="1"
                            max="50"
                        />
                        <Form.Text className="text-muted">
                            Profundidade máxima das árvores. Valores entre 1 e 50.
                        </Form.Text>
                    </Form.Group>
                </>
            );
        } else if (modelType === 'logistic_regression') {
            return (
                <>
                    <Form.Group className="mb-3">
                        <Form.Label>Parâmetro de Regularização (C)</Form.Label>
                        <Form.Control
                            type="number"
                            value={currentParams.C || 1.0}
                            onChange={(e) => handleParameterChange('C', parseFloat(e.target.value))}
                            min="0.1"
                            max="10"
                            step="0.1"
                        />
                        <Form.Text className="text-muted">
                            Inverso da força de regularização. Valores entre 0.1 e 10.
                        </Form.Text>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Número Máximo de Iterações (max_iter)</Form.Label>
                        <Form.Control
                            type="number"
                            value={currentParams.max_iter || 1000}
                            onChange={(e) => handleParameterChange('max_iter', parseInt(e.target.value))}
                            min="100"
                            max="10000"
                            step="100"
                        />
                        <Form.Text className="text-muted">
                            Número máximo de iterações até convergência. Valores entre 100 e 10000.
                        </Form.Text>
                    </Form.Group>
                </>
            );
        }

        return null;
    };

    if (configLoading) {
        return (
            <div className="loading-spinner">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    return (
        <div>
            <h2 className="mb-4">Treinamento do Modelo</h2>

            <Row>
                <Col lg={8}>
                    <Card className="dashboard-card">
                        <Card.Body>
                            <Card.Title>Configuração do Modelo</Card.Title>

                            <Alert variant="info" className="mt-3">
                                Você pode configurar os parâmetros do modelo e retreiná-lo para obter melhores resultados.
                                O novo modelo substituirá o modelo atual e atualizará as métricas.
                            </Alert>

                            <Form onSubmit={handleSubmit} className="model-config-form mt-4">
                                <Form.Group className="mb-4">
                                    <Form.Label><strong>Tipo de Modelo</strong></Form.Label>
                                    <Form.Select
                                        value={modelType}
                                        onChange={handleModelTypeChange}
                                        className="mb-3"
                                    >
                                        <option value="random_forest">Random Forest Classifier</option>
                                        <option value="logistic_regression">Regressão Logística</option>
                                    </Form.Select>

                                    <Form.Text className="text-muted">
                                        Selecione o algoritmo de machine learning que será utilizado no treinamento.
                                    </Form.Text>
                                </Form.Group>

                                <h5 className="mb-3">Parâmetros do Modelo</h5>
                                {renderParameters()}

                                <Form.Group className="mb-3">
                                    <Form.Label>Random State</Form.Label>
                                    <Form.Control
                                        type="number"
                                        value={currentParams.random_state || 42}
                                        onChange={(e) => handleParameterChange('random_state', parseInt(e.target.value))}
                                        min="0"
                                    />
                                    <Form.Text className="text-muted">
                                        Semente para geração de números aleatórios. Mantém a reprodutibilidade dos resultados.
                                    </Form.Text>
                                </Form.Group>

                                <div className="d-grid gap-2 mt-4">
                                    <Button variant="primary" type="submit" disabled={loading}>
                                        {loading ? 'Treinando Modelo...' : 'Treinar Modelo'}
                                    </Button>
                                </div>

                                {error && (
                                    <Alert variant="danger" className="mt-3">
                                        {error}
                                    </Alert>
                                )}

                                {success && (
                                    <Alert variant="success" className="mt-3">
                                        {success}
                                    </Alert>
                                )}
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col lg={4}>
                    <Card className="dashboard-card">
                        <Card.Body>
                            <Card.Title>Informações</Card.Title>

                            <div className="mt-3">
                                <h5>Random Forest</h5>
                                <p>
                                    Um algoritmo de ensemble que utiliza múltiplas árvores de decisão para melhorar a precisão
                                    e controlar o overfitting. Bom para problemas não-lineares e com features de diferentes tipos.
                                </p>

                                <h6>Parâmetros importantes:</h6>
                                <ul>
                                    <li><strong>n_estimators</strong>: Mais árvores geralmente melhoram a performance, mas aumentam o tempo de treinamento.</li>
                                    <li><strong>max_depth</strong>: Limita a profundidade das árvores, ajudando a evitar overfitting.</li>
                                </ul>
                            </div>

                            <hr />

                            <div>
                                <h5>Regressão Logística</h5>
                                <p>
                                    Um algoritmo linear para classificação binária ou multiclasse. Funciona bem com datasets
                                    lineares e é fácil de interpretar. Pode ser mais rápido que modelos mais complexos.
                                </p>

                                <h6>Parâmetros importantes:</h6>
                                <ul>
                                    <li><strong>C</strong>: Controla a regularização. Valores menores aumentam a regularização.</li>
                                    <li><strong>max_iter</strong>: Número máximo de iterações para o algoritmo convergir.</li>
                                </ul>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default ModelTraining; 