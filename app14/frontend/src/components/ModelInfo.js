import React, { useState } from 'react';
import { Card, Row, Col, Button, Alert, Spinner, Form, Badge, Table } from 'react-bootstrap';
import { FaChartBar, FaBrain, FaUpload, FaCheck, FaExclamationTriangle } from 'react-icons/fa';

const ModelInfo = ({ apiUrl, modeloInfo }) => {
    const [loading, setLoading] = useState(false);
    const [treinandoModelo, setTreinandoModelo] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [arquivo, setArquivo] = useState(null);
    const [visualizacoes, setVisualizacoes] = useState({
        histogram: null,
        boxplot: null,
        complexity: null
    });

    // Treinar modelo com dados existentes
    const treinarModelo = async () => {
        try {
            setTreinandoModelo(true);
            setError(null);
            setSuccess(null);

            const response = await fetch(`${apiUrl}/treinar-modelo/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message);
            }

            setSuccess(`Modelo treinado com sucesso! ${data.message}`);

            // Reload page after 2 seconds to update model info
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            console.error('Erro ao treinar modelo:', error);
            setError(error.message);
        } finally {
            setTreinandoModelo(false);
        }
    };

    // Manipular seleção de arquivo
    const handleFileChange = (e) => {
        if (e.target.files.length > 0) {
            setArquivo(e.target.files[0]);
        }
    };

    // Fazer upload de arquivo CSV para treinamento
    const uploadArquivo = async (e) => {
        e.preventDefault();

        if (!arquivo) {
            setError('Por favor, selecione um arquivo CSV para upload.');
            return;
        }

        if (!arquivo.name.endsWith('.csv')) {
            setError('O arquivo deve estar no formato CSV.');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setSuccess(null);

            const formData = new FormData();
            formData.append('file', arquivo);

            const response = await fetch(`${apiUrl}/upload-dados-treinamento/`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message);
            }

            setSuccess(`Upload realizado com sucesso! ${data.message}`);
            setArquivo(null);

            // Limpar input de arquivo
            document.getElementById('formFile').value = '';

            // Reload page after 2 seconds to update model info
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            console.error('Erro ao fazer upload:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    // Carregar visualização
    const carregarVisualizacao = async (tipo) => {
        try {
            setLoading(true);
            setError(null);

            const imgUrl = `${apiUrl}/visualizacoes/${tipo}`;

            // Verificar se a imagem está acessível
            const response = await fetch(imgUrl, { method: 'HEAD' });

            if (!response.ok) {
                throw new Error(`Não foi possível carregar a visualização. ${response.statusText}`);
            }

            // Atualizar URL da visualização com timestamp para evitar cache
            setVisualizacoes(prev => ({
                ...prev,
                [tipo]: `${imgUrl}?t=${new Date().getTime()}`
            }));
        } catch (error) {
            console.error(`Erro ao carregar visualização ${tipo}:`, error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    // Formatar métricas para exibição
    const formatMetric = (value) => {
        if (value === undefined || value === null) return 'N/A';
        return typeof value === 'number' ? value.toFixed(4) : value;
    };

    return (
        <div>
            <h1 className="mb-4 text-center">Informações do Modelo</h1>

            {error && <Alert variant="danger">{error}</Alert>}
            {success && <Alert variant="success">{success}</Alert>}

            <Row>
                <Col md={6}>
                    <Card className="mb-4">
                        <Card.Header className="d-flex align-items-center">
                            <FaBrain className="me-2" />
                            Status do Modelo
                        </Card.Header>
                        <Card.Body>
                            {!modeloInfo ? (
                                <div className="text-center">
                                    <Spinner animation="border" variant="primary" />
                                    <p>Carregando informações do modelo...</p>
                                </div>
                            ) : (
                                <div>
                                    <div className="mb-4 text-center">
                                        <h5>
                                            Status:
                                            {modeloInfo.status === 'treinado' ? (
                                                <Badge bg="success" className="ms-2">Treinado</Badge>
                                            ) : (
                                                <Badge bg="warning" className="ms-2">Não Treinado</Badge>
                                            )}
                                        </h5>

                                        {modeloInfo.status === 'treinado' && (
                                            <div className="mt-3">
                                                <p><strong>Tipo de Modelo:</strong> {modeloInfo.tipo_modelo}</p>
                                                <p><strong>Features:</strong> {modeloInfo.features.join(', ')}</p>

                                                {modeloInfo.tipos_solicitacao && modeloInfo.tipos_solicitacao.length > 0 && (
                                                    <div>
                                                        <p><strong>Tipos de Solicitação:</strong></p>
                                                        <ul className="text-start">
                                                            {modeloInfo.tipos_solicitacao.map((tipo, index) => (
                                                                <li key={index}>{tipo}</li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {modeloInfo.metricas && (
                                                    <div className="mt-3">
                                                        <h6>Métricas de Desempenho</h6>
                                                        <Table striped bordered size="sm" className="mt-2">
                                                            <thead>
                                                                <tr>
                                                                    <th>Métrica</th>
                                                                    <th>Valor</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                <tr>
                                                                    <td>MSE (Erro Quadrático Médio)</td>
                                                                    <td>{formatMetric(modeloInfo.metricas?.mse)}</td>
                                                                </tr>
                                                                <tr>
                                                                    <td>RMSE (Raiz do Erro Quadrático Médio)</td>
                                                                    <td>{formatMetric(modeloInfo.metricas?.rmse)}</td>
                                                                </tr>
                                                                <tr>
                                                                    <td>MAE (Erro Absoluto Médio)</td>
                                                                    <td>{formatMetric(modeloInfo.metricas?.mae)}</td>
                                                                </tr>
                                                                <tr>
                                                                    <td>R² (Coeficiente de Determinação)</td>
                                                                    <td>{formatMetric(modeloInfo.metricas?.r2)}</td>
                                                                </tr>
                                                            </tbody>
                                                        </Table>
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {modeloInfo.status !== 'treinado' && (
                                            <div className="mt-3">
                                                <Alert variant="info">
                                                    <FaExclamationTriangle className="me-2" />
                                                    {modeloInfo.message || "O modelo ainda não foi treinado. Utilize uma das opções abaixo para treinar o modelo."}
                                                </Alert>
                                            </div>
                                        )}
                                    </div>

                                    <div className="d-grid gap-2">
                                        <Button
                                            variant="primary"
                                            onClick={treinarModelo}
                                            disabled={treinandoModelo}
                                        >
                                            {treinandoModelo ? (
                                                <>
                                                    <Spinner
                                                        as="span"
                                                        animation="border"
                                                        size="sm"
                                                        role="status"
                                                        aria-hidden="true"
                                                        className="me-2"
                                                    />
                                                    Treinando...
                                                </>
                                            ) : (
                                                <>
                                                    <FaBrain className="me-2" />
                                                    Treinar Modelo com Dados Existentes
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </Card.Body>
                    </Card>

                    <Card className="mb-4">
                        <Card.Header>
                            <FaUpload className="me-2" />
                            Upload de Dados para Treinamento
                        </Card.Header>
                        <Card.Body>
                            <Form onSubmit={uploadArquivo}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Selecionar Arquivo CSV</Form.Label>
                                    <Form.Control
                                        type="file"
                                        id="formFile"
                                        accept=".csv"
                                        onChange={handleFileChange}
                                    />
                                    <Form.Text className="text-muted">
                                        O arquivo CSV deve conter as colunas: tipo_solicitacao, complexidade, tempo_atendimento
                                    </Form.Text>
                                </Form.Group>
                                <Button
                                    variant="success"
                                    type="submit"
                                    disabled={loading || !arquivo}
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
                                            Enviando...
                                        </>
                                    ) : (
                                        <>
                                            <FaUpload className="me-2" />
                                            Enviar e Treinar Modelo
                                        </>
                                    )}
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={6}>
                    <Card className="mb-4">
                        <Card.Header>
                            <FaChartBar className="me-2" />
                            Visualizações
                        </Card.Header>
                        <Card.Body>
                            {!modeloInfo || modeloInfo.status !== 'treinado' ? (
                                <Alert variant="warning">
                                    O modelo precisa estar treinado para gerar visualizações.
                                </Alert>
                            ) : (
                                <div>
                                    <div className="mb-3">
                                        <Row>
                                            <Col md={4}>
                                                <Button
                                                    variant="outline-primary"
                                                    className="w-100 mb-2"
                                                    onClick={() => carregarVisualizacao('histogram')}
                                                    disabled={loading}
                                                >
                                                    Distribuição de Tempo
                                                </Button>
                                            </Col>
                                            <Col md={4}>
                                                <Button
                                                    variant="outline-primary"
                                                    className="w-100 mb-2"
                                                    onClick={() => carregarVisualizacao('boxplot')}
                                                    disabled={loading}
                                                >
                                                    Tempo por Tipo
                                                </Button>
                                            </Col>
                                            <Col md={4}>
                                                <Button
                                                    variant="outline-primary"
                                                    className="w-100 mb-2"
                                                    onClick={() => carregarVisualizacao('complexity')}
                                                    disabled={loading}
                                                >
                                                    Tempo por Complexidade
                                                </Button>
                                            </Col>
                                        </Row>
                                    </div>

                                    {loading && (
                                        <div className="text-center my-4">
                                            <Spinner animation="border" variant="primary" />
                                            <p>Carregando visualização...</p>
                                        </div>
                                    )}

                                    {visualizacoes.histogram && (
                                        <div className="mb-4">
                                            <h5 className="text-center mb-3">Distribuição de Tempo de Atendimento</h5>
                                            <div className="text-center">
                                                <img
                                                    src={visualizacoes.histogram}
                                                    alt="Distribuição de Tempo de Atendimento"
                                                    className="img-fluid border rounded"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {visualizacoes.boxplot && (
                                        <div className="mb-4">
                                            <h5 className="text-center mb-3">Tempo por Tipo de Solicitação</h5>
                                            <div className="text-center">
                                                <img
                                                    src={visualizacoes.boxplot}
                                                    alt="Tempo por Tipo de Solicitação"
                                                    className="img-fluid border rounded"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {visualizacoes.complexity && (
                                        <div className="mb-4">
                                            <h5 className="text-center mb-3">Tempo por Nível de Complexidade</h5>
                                            <div className="text-center">
                                                <img
                                                    src={visualizacoes.complexity}
                                                    alt="Tempo por Nível de Complexidade"
                                                    className="img-fluid border rounded"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {!visualizacoes.histogram && !visualizacoes.boxplot && !visualizacoes.complexity && !loading && (
                                        <Alert variant="info">
                                            <FaChartBar className="me-2" />
                                            Clique em um dos botões acima para visualizar gráficos relacionados aos dados de tempo de atendimento.
                                        </Alert>
                                    )}
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default ModelInfo; 