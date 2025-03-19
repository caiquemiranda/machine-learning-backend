import React, { useState } from 'react';
import { Card, Form, Button, Alert, Row, Col } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { UserService } from '../services/api';

const Profile = () => {
    const { user, logout } = useAuth();

    const [formData, setFormData] = useState({
        email: user?.email || '',
        full_name: user?.full_name || '',
        password: '',
        confirmPassword: ''
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Resetar mensagens
        setError(null);
        setSuccess(null);

        // Validação de senhas
        if (formData.password && formData.password !== formData.confirmPassword) {
            setError('As senhas não coincidem.');
            return;
        }

        // Validar formato de email (simples)
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (formData.email && !emailRegex.test(formData.email)) {
            setError('Por favor, forneça um email válido.');
            return;
        }

        try {
            setLoading(true);

            // Preparar dados para atualização (apenas campos alterados)
            const updateData = {};

            if (formData.email !== user.email) {
                updateData.email = formData.email;
            }

            if (formData.full_name !== user.full_name) {
                updateData.full_name = formData.full_name;
            }

            if (formData.password) {
                updateData.password = formData.password;
            }

            // Só enviar se houver alterações
            if (Object.keys(updateData).length > 0) {
                await UserService.updateProfile(updateData);
                setSuccess('Perfil atualizado com sucesso!');
            } else {
                setSuccess('Nenhuma alteração foi feita.');
            }
        } catch (err) {
            console.error('Erro ao atualizar perfil:', err);
            setError(err.response?.data?.detail || 'Erro ao atualizar perfil. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2 className="page-title">Meu Perfil</h2>

            <Row>
                <Col md={6} className="mx-auto">
                    <Card>
                        <Card.Header>
                            <h5 className="mb-0">Informações do Usuário</h5>
                        </Card.Header>
                        <Card.Body>
                            {error && <Alert variant="danger">{error}</Alert>}
                            {success && <Alert variant="success">{success}</Alert>}

                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Nome de usuário</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={user?.username || ''}
                                        disabled
                                    />
                                    <Form.Text className="text-muted">
                                        O nome de usuário não pode ser alterado.
                                    </Form.Text>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Email</Form.Label>
                                    <Form.Control
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleChange}
                                        required
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Nome completo</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="full_name"
                                        value={formData.full_name}
                                        onChange={handleChange}
                                    />
                                </Form.Group>

                                <hr className="my-4" />

                                <Form.Group className="mb-3">
                                    <Form.Label>Nova senha</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="password"
                                        value={formData.password}
                                        onChange={handleChange}
                                        placeholder="Deixe em branco para manter a senha atual"
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Confirmar nova senha</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        placeholder="Confirme a nova senha"
                                    />
                                </Form.Group>

                                <div className="d-grid gap-2">
                                    <Button
                                        variant="primary"
                                        type="submit"
                                        disabled={loading}
                                    >
                                        {loading ? 'Salvando...' : 'Salvar Alterações'}
                                    </Button>

                                    <Button
                                        variant="outline-danger"
                                        onClick={logout}
                                    >
                                        Sair da Conta
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>

                    <Card className="mt-4">
                        <Card.Header className="bg-info text-white">
                            <h5 className="mb-0">Informações da Conta</h5>
                        </Card.Header>
                        <Card.Body>
                            <Row>
                                <Col sm={6}>
                                    <p><strong>Data de criação:</strong></p>
                                    <p className="text-muted">
                                        {user?.created_at ? new Date(user.created_at).toLocaleDateString('pt-BR') : 'N/A'}
                                    </p>
                                </Col>
                                <Col sm={6}>
                                    <p><strong>Último acesso:</strong></p>
                                    <p className="text-muted">
                                        {user?.updated_at ? new Date(user.updated_at).toLocaleDateString('pt-BR') : 'N/A'}
                                    </p>
                                </Col>
                            </Row>

                            <Row>
                                <Col sm={6}>
                                    <p><strong>Tipo de conta:</strong></p>
                                    <p className="text-muted">
                                        {user?.is_admin ? 'Administrador' : 'Usuário padrão'}
                                    </p>
                                </Col>
                                <Col sm={6}>
                                    <p><strong>Status:</strong></p>
                                    <p className="text-muted">
                                        {user?.is_active ? 'Ativo' : 'Inativo'}
                                    </p>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default Profile; 