import React, { useState } from 'react';
import { Card, Form, Button, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const { login, error, setError } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Limpar erro anterior
        setError(null);

        // Validação básica
        if (!username || !password) {
            setError('Por favor, preencha todos os campos.');
            return;
        }

        try {
            setLoading(true);
            const success = await login(username, password);

            if (success) {
                navigate('/dashboard');
            }
        } catch (error) {
            console.error('Erro no login:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <Card className="auth-card">
                <Card.Body>
                    <h2 className="text-center mb-4">Login</h2>

                    {error && <Alert variant="danger">{error}</Alert>}

                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3" controlId="username">
                            <Form.Label>Nome de usuário</Form.Label>
                            <Form.Control
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Digite seu nome de usuário"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="password">
                            <Form.Label>Senha</Form.Label>
                            <Form.Control
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Digite sua senha"
                                required
                            />
                        </Form.Group>

                        <Button
                            variant="primary"
                            type="submit"
                            className="w-100 mt-3"
                            disabled={loading}
                        >
                            {loading ? 'Entrando...' : 'Entrar'}
                        </Button>
                    </Form>

                    <div className="text-center mt-3">
                        <p>
                            Não tem uma conta? <Link to="/register">Cadastre-se</Link>
                        </p>
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

export default Login; 