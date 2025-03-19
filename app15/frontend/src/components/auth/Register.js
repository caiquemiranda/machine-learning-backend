import React, { useState } from 'react';
import { Card, Form, Button, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        full_name: '',
        password: '',
        confirmPassword: ''
    });
    const [loading, setLoading] = useState(false);

    const { register, error, setError } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Limpar erro anterior
        setError(null);

        // Validação básica
        if (!formData.username || !formData.email || !formData.password || !formData.confirmPassword) {
            setError('Por favor, preencha todos os campos obrigatórios.');
            return;
        }

        // Validar senhas
        if (formData.password !== formData.confirmPassword) {
            setError('As senhas não coincidem.');
            return;
        }

        // Validar formato de email (simples)
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setError('Por favor, forneça um email válido.');
            return;
        }

        try {
            setLoading(true);

            // Preparar dados para registro
            const userData = {
                username: formData.username,
                email: formData.email,
                full_name: formData.full_name,
                password: formData.password
            };

            const success = await register(userData);

            if (success) {
                navigate('/dashboard');
            }
        } catch (error) {
            console.error('Erro no registro:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <Card className="auth-card">
                <Card.Body>
                    <h2 className="text-center mb-4">Criar Conta</h2>

                    {error && <Alert variant="danger">{error}</Alert>}

                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3" controlId="username">
                            <Form.Label>Nome de usuário</Form.Label>
                            <Form.Control
                                type="text"
                                name="username"
                                value={formData.username}
                                onChange={handleChange}
                                placeholder="Digite seu nome de usuário"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="email">
                            <Form.Label>Email</Form.Label>
                            <Form.Control
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="Digite seu email"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="fullName">
                            <Form.Label>Nome completo</Form.Label>
                            <Form.Control
                                type="text"
                                name="full_name"
                                value={formData.full_name}
                                onChange={handleChange}
                                placeholder="Digite seu nome completo"
                            />
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="password">
                            <Form.Label>Senha</Form.Label>
                            <Form.Control
                                type="password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="Digite sua senha"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="confirmPassword">
                            <Form.Label>Confirmar senha</Form.Label>
                            <Form.Control
                                type="password"
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                placeholder="Confirme sua senha"
                                required
                            />
                        </Form.Group>

                        <Button
                            variant="primary"
                            type="submit"
                            className="w-100 mt-3"
                            disabled={loading}
                        >
                            {loading ? 'Registrando...' : 'Registrar'}
                        </Button>
                    </Form>

                    <div className="text-center mt-3">
                        <p>
                            Já tem uma conta? <Link to="/login">Faça login</Link>
                        </p>
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

export default Register; 