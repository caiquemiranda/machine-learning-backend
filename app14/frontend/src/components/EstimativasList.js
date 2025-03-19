import React, { useState, useEffect } from 'react';
import { Table, Card, Badge, Form, Row, Col, Button, Spinner, Alert } from 'react-bootstrap';
import { FaSearch, FaFilter, FaSync } from 'react-icons/fa';

const EstimativasList = ({ apiUrl }) => {
    const [estimativas, setEstimativas] = useState([]);
    const [tiposSolicitacao, setTiposSolicitacao] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filtro, setFiltro] = useState({
        tipoSolicitacaoId: '',
        limit: 100
    });

    // Carregar tipos de solicitação
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
                console.error('Erro ao carregar tipos de solicitação:', error);
                setError('Não foi possível carregar os tipos de solicitação.');
            }
        };

        fetchTiposSolicitacao();
    }, [apiUrl]);

    // Buscar estimativas
    const fetchEstimativas = async () => {
        try {
            setLoading(true);
            setError(null);

            let url = `${apiUrl}/estimativas/?limit=${filtro.limit}`;
            if (filtro.tipoSolicitacaoId) {
                url += `&tipo_solicitacao_id=${filtro.tipoSolicitacaoId}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Erro ao carregar estimativas: ${response.statusText}`);
            }

            const data = await response.json();
            setEstimativas(data);
        } catch (error) {
            console.error('Erro ao carregar estimativas:', error);
            setError('Não foi possível carregar as estimativas. Por favor, tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    // Carregar estimativas ao iniciar
    useEffect(() => {
        fetchEstimativas();
    }, [apiUrl]); // eslint-disable-line react-hooks/exhaustive-deps

    // Atualizar filtro
    const handleFiltroChange = (e) => {
        const { name, value } = e.target;
        setFiltro({
            ...filtro,
            [name]: value
        });
    };

    // Aplicar filtro
    const aplicarFiltro = (e) => {
        e.preventDefault();
        fetchEstimativas();
    };

    // Formatar data
    const formatarData = (dataString) => {
        const data = new Date(dataString);
        return new Intl.DateTimeFormat('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(data);
    };

    // Renderizar badge de complexidade
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

    // Obter nome do tipo de solicitação pelo ID
    const getTipoSolicitacaoNome = (id) => {
        const tipo = tiposSolicitacao.find(t => t.id === id);
        return tipo ? tipo.nome : 'Desconhecido';
    };

    return (
        <div>
            <h1 className="mb-4 text-center">Histórico de Estimativas</h1>

            <Card className="mb-4">
                <Card.Header>
                    <FaFilter className="me-2" />
                    Filtros
                </Card.Header>
                <Card.Body>
                    <Form onSubmit={aplicarFiltro}>
                        <Row className="align-items-end">
                            <Col md={5}>
                                <Form.Group>
                                    <Form.Label>Tipo de Solicitação</Form.Label>
                                    <Form.Select
                                        name="tipoSolicitacaoId"
                                        value={filtro.tipoSolicitacaoId}
                                        onChange={handleFiltroChange}
                                    >
                                        <option value="">Todos</option>
                                        {tiposSolicitacao.map((tipo) => (
                                            <option key={tipo.id} value={tipo.id}>
                                                {tipo.nome}
                                            </option>
                                        ))}
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={4}>
                                <Form.Group>
                                    <Form.Label>Limite de Registros</Form.Label>
                                    <Form.Select
                                        name="limit"
                                        value={filtro.limit}
                                        onChange={handleFiltroChange}
                                    >
                                        <option value="10">10 registros</option>
                                        <option value="25">25 registros</option>
                                        <option value="50">50 registros</option>
                                        <option value="100">100 registros</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={3} className="d-flex justify-content-end">
                                <Button variant="primary" type="submit" className="me-2">
                                    <FaSearch className="me-1" /> Filtrar
                                </Button>
                                <Button variant="outline-secondary" onClick={fetchEstimativas}>
                                    <FaSync className="me-1" /> Atualizar
                                </Button>
                            </Col>
                        </Row>
                    </Form>
                </Card.Body>
            </Card>

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="table-container">
                {loading ? (
                    <div className="text-center py-5">
                        <Spinner animation="border" variant="primary" />
                        <p className="mt-2">Carregando estimativas...</p>
                    </div>
                ) : estimativas.length === 0 ? (
                    <Alert variant="info">
                        Nenhuma estimativa encontrada com os critérios atuais.
                    </Alert>
                ) : (
                    <Table striped hover responsive>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tipo de Solicitação</th>
                                <th>Complexidade</th>
                                <th>Tempo Estimado</th>
                                <th>Tempo Real</th>
                                <th>Data</th>
                                <th>Observações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {estimativas.map((estimativa) => (
                                <tr key={estimativa.id}>
                                    <td>{estimativa.id}</td>
                                    <td>{getTipoSolicitacaoNome(estimativa.tipo_solicitacao_id)}</td>
                                    <td className="text-center">{renderComplexityBadge(estimativa.complexidade)}</td>
                                    <td>{estimativa.tempo_estimado.toFixed(1)} min</td>
                                    <td>
                                        {estimativa.tempo_real
                                            ? `${estimativa.tempo_real.toFixed(1)} min`
                                            : <span className="text-muted">N/D</span>
                                        }
                                    </td>
                                    <td>{formatarData(estimativa.data_criacao)}</td>
                                    <td>
                                        {estimativa.observacoes
                                            ? estimativa.observacoes
                                            : <span className="text-muted">--</span>
                                        }
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                )}
            </div>
        </div>
    );
};

export default EstimativasList; 