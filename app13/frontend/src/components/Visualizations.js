import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Alert, Spinner, Button } from 'react-bootstrap';
import { FaSync } from 'react-icons/fa';
import { getConfusionMatrix, getFeatureImportance } from '../api';

const Visualizations = () => {
    const [confusionMatrix, setConfusionMatrix] = useState(null);
    const [featureImportance, setFeatureImportance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchVisualizations = async () => {
        setLoading(true);
        try {
            const [matrixData, importanceData] = await Promise.all([
                getConfusionMatrix(),
                getFeatureImportance().catch(err => {
                    // Pode falhar para modelos que não suportam importância de features
                    console.warn('Erro ao buscar importância de features:', err);
                    return null;
                })
            ]);

            setConfusionMatrix(matrixData);
            setFeatureImportance(importanceData);
            setError(null);
        } catch (err) {
            console.error('Erro ao buscar visualizações:', err);
            setError('Não foi possível carregar as visualizações. Verifique se o servidor está em execução.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVisualizations();
    }, []);

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Visualizações do Modelo</h2>
                <Button
                    variant="outline-primary"
                    onClick={fetchVisualizations}
                    disabled={loading}
                    className="d-flex align-items-center"
                >
                    <FaSync className="me-2" />
                    Atualizar
                </Button>
            </div>

            {error && (
                <Alert variant="danger">
                    {error}
                </Alert>
            )}

            <Row>
                {confusionMatrix && (
                    <Col lg={6}>
                        <Card className="dashboard-card mb-4">
                            <Card.Body>
                                <Card.Title>Matriz de Confusão</Card.Title>
                                <Card.Text>
                                    Esta matriz mostra o desempenho do modelo na classificação, comparando predições com valores reais.
                                </Card.Text>
                                <div className="d-flex justify-content-center mt-4">
                                    <img
                                        src={`data:image/png;base64,${confusionMatrix.image}`}
                                        alt="Matriz de Confusão"
                                        className="img-fluid"
                                        style={{ maxHeight: '400px' }}
                                    />
                                </div>
                                <div className="mt-3">
                                    <h6>Classes:</h6>
                                    <ul>
                                        {confusionMatrix.classes.map((cls, index) => (
                                            <li key={index}>
                                                <span className="badge bg-secondary me-2">{index}</span>
                                                {cls === 'saudavel' ? 'Saudável' :
                                                    cls === 'risco_baixo' ? 'Risco Baixo' :
                                                        cls === 'risco_moderado' ? 'Risco Moderado' :
                                                            cls === 'risco_alto' ? 'Risco Alto' : cls}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div className="text-muted mt-2">
                                    <small>
                                        A diagonal principal (de cima-esquerda para baixo-direita) mostra as classificações corretas.
                                        Os demais valores representam erros de classificação.
                                    </small>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                )}

                {featureImportance ? (
                    <Col lg={6}>
                        <Card className="dashboard-card mb-4">
                            <Card.Body>
                                <Card.Title>Importância das Features</Card.Title>
                                <Card.Text>
                                    Este gráfico mostra quais características têm maior impacto nas predições do modelo.
                                </Card.Text>
                                <div className="d-flex justify-content-center mt-4">
                                    <img
                                        src={`data:image/png;base64,${featureImportance.image}`}
                                        alt="Importância das Features"
                                        className="img-fluid"
                                        style={{ maxHeight: '400px' }}
                                    />
                                </div>
                                <div className="mt-3">
                                    <h6>Features (em ordem de importância):</h6>
                                    <ul>
                                        {featureImportance.features.map((feature, index) => (
                                            <li key={index}>
                                                <strong>
                                                    {feature === 'idade' ? 'Idade' :
                                                        feature === 'pressao_arterial' ? 'Pressão Arterial' :
                                                            feature === 'glicose' ? 'Nível de Glicose' :
                                                                feature === 'freq_cardiaca' ? 'Frequência Cardíaca' :
                                                                    feature === 'imc' ? 'IMC' :
                                                                        feature === 'exercicio_semanal' ? 'Exercício Semanal' :
                                                                            feature === 'fumante' ? 'Fumante' : feature}
                                                </strong>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div className="text-muted mt-2">
                                    <small>
                                        Features com valores mais altos têm maior influência nas predições do modelo.
                                    </small>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                ) : (
                    !error && (
                        <Col lg={6}>
                            <Card className="dashboard-card mb-4">
                                <Card.Body>
                                    <Card.Title>Importância das Features</Card.Title>
                                    <Alert variant="info">
                                        O modelo atual não suporta visualização de importância de features.
                                        Tente usar um modelo do tipo Random Forest que oferece esta funcionalidade.
                                    </Alert>
                                </Card.Body>
                            </Card>
                        </Col>
                    )
                )}
            </Row>

            <Card className="dashboard-card">
                <Card.Body>
                    <Card.Title>Interpretando as Visualizações</Card.Title>

                    <h5 className="mt-4">Matriz de Confusão</h5>
                    <p>
                        A matriz de confusão é uma ferramenta essencial para avaliar o desempenho de modelos de classificação.
                        Ela compara as predições do modelo com os valores reais, organizados em uma tabela.
                    </p>
                    <ul>
                        <li><strong>Diagonal principal:</strong> Representa acertos (predições corretas)</li>
                        <li><strong>Fora da diagonal:</strong> Representa erros (predições incorretas)</li>
                    </ul>
                    <p>
                        Um modelo ideal teria valores altos apenas na diagonal principal, indicando poucos erros de classificação.
                    </p>

                    <h5 className="mt-4">Importância das Features</h5>
                    <p>
                        Este gráfico mostra o quanto cada feature contribui para as decisões do modelo.
                        Features com maior importância têm maior influência no resultado final da classificação.
                    </p>
                    <p>
                        Você pode usar esta informação para:
                    </p>
                    <ul>
                        <li>Entender quais fatores são mais relevantes para o diagnóstico</li>
                        <li>Identificar features redundantes ou irrelevantes</li>
                        <li>Melhorar a coleta de dados, focando nas features mais importantes</li>
                    </ul>
                </Card.Body>
            </Card>
        </div>
    );
};

export default Visualizations; 