import React, { useState, useEffect } from 'react';
import { Table, Card, Form, Button, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { FaPlus, FaSave, FaTimes } from 'react-icons/fa';

const TiposSolicitacao = ({ apiUrl }) => {
    const [tiposSolicitacao, setTiposSolicitacao] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [novoTipo, setNovoTipo] = useState({
        nome: '',
        descricao: ''
    });
    const [showForm, setShowForm] = useState(false);

    // Carregar tipos de solicitação
    const carregarTipos = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch(`${apiUrl}/tipos-solicitacao/`);
            if (!response.ok) {
                throw new Error(`Erro ao carregar tipos de solicitação: ${response.statusText}`);
            }

            const data = await response.json();
            setTiposSolicitacao(data);
        } catch (error) {
            console.error('Erro ao carregar tipos de solicitação:', error);
            setError('Não foi possível carregar os tipos de solicitação. Por favor, tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    // Carregar tipos ao iniciar
    useEffect(() => {
        carregarTipos();
    }, [apiUrl]);

    // Manipulador de mudanças no formulário
    const handleChange = (e) => {
        const { name, value } = e.target;
        setNovoTipo({
            ...novoTipo,
            [name]: value
        });
    };

    // Limpar o formulário
    const limparFormulario = () => {
        setNovoTipo({
            nome: '',
            descricao: ''
        });
    };

    // Adicionar novo tipo
    const adicionarTipo = async (e) => {
        e.preventDefault();

        // Validar entrada
        if (!novoTipo.nome.trim()) {
            setError('O nome do tipo de solicitação é obrigatório.');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setSuccess(null);

            const response = await fetch(`${apiUrl}/tipos-solicitacao/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nome: novoTipo.nome,
                    descricao: novoTipo.descricao || null
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao criar tipo de solicitação');
            }

            // Recarregar a lista
            await carregarTipos();

            // Limpar formulário e exibir mensagem de sucesso
            limparFormulario();
            setShowForm(false);
            setSuccess('Tipo de solicitação adicionado com sucesso!');

            // Limpar mensagem de sucesso após 3 segundos
            setTimeout(() => {
                setSuccess(null);
            }, 3000);
        } catch (error) {
            console.error('Erro ao adicionar tipo de solicitação:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    // Toggle do formulário
    const toggleForm = () => {
        setShowForm(!showForm);
        if (!showForm) {
            limparFormulario();
            setError(null);
        }
    };

    return (
        <div>
            <h1 className="mb-4 text-center">Tipos de Solicitação</h1>

            {error && <Alert variant="danger">{error}</Alert>}
            {success && <Alert variant="success">{success}</Alert>}

            <Card className="mb-4">
                <Card.Header className="d-flex justify-content-between align-items-center">
                    <span>Gerenciar Tipos de Solicitação</span>
                    <Button
                        variant={showForm ? "danger" : "primary"}
                        size="sm"
                        onClick={toggleForm}
                    >
                        {showForm ? (
                            <>
                                <FaTimes className="me-1" /> Cancelar
                            </>
                        ) : (
                            <>
                                <FaPlus className="me-1" /> Novo Tipo
                            </>
                        )}
                    </Button>
                </Card.Header>

                {showForm && (
                    <Card.Body>
                        <Form onSubmit={adicionarTipo}>
                            <Row>
                                <Col md={4}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Nome do Tipo <span className="text-danger">*</span></Form.Label>
                                        <Form.Control
                                            type="text"
                                            name="nome"
                                            value={novoTipo.nome}
                                            onChange={handleChange}
                                            placeholder="Ex.: Suporte Técnico"
                                            required
                                        />
                                    </Form.Group>
                                </Col>
                                <Col md={6}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Descrição</Form.Label>
                                        <Form.Control
                                            type="text"
                                            name="descricao"
                                            value={novoTipo.descricao}
                                            onChange={handleChange}
                                            placeholder="Descrição do tipo de solicitação"
                                        />
                                    </Form.Group>
                                </Col>
                                <Col md={2} className="d-flex align-items-end">
                                    <Button
                                        variant="success"
                                        type="submit"
                                        className="mb-3 w-100"
                                        disabled={loading || !novoTipo.nome.trim()}
                                    >
                                        <FaSave className="me-1" /> Salvar
                                    </Button>
                                </Col>
                            </Row>
                        </Form>
                    </Card.Body>
                )}
            </Card>

            <div className="table-container">
                {loading ? (
                    <div className="text-center py-5">
                        <Spinner animation="border" variant="primary" />
                        <p className="mt-2">Carregando tipos de solicitação...</p>
                    </div>
                ) : tiposSolicitacao.length === 0 ? (
                    <Alert variant="info">
                        Nenhum tipo de solicitação cadastrado. Adicione um novo tipo para começar.
                    </Alert>
                ) : (
                    <Table striped hover responsive>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nome</th>
                                <th>Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tiposSolicitacao.map((tipo) => (
                                <tr key={tipo.id}>
                                    <td>{tipo.id}</td>
                                    <td>{tipo.nome}</td>
                                    <td>{tipo.descricao || <span className="text-muted">--</span>}</td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                )}
            </div>
        </div>
    );
};

export default TiposSolicitacao; 