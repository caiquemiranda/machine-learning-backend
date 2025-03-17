import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import PredictionForm from './components/PredictionForm';
import PredictionHistory from './components/PredictionHistory';

function App() {
    return (
        <Container className="mt-5">
            <Row className="justify-content-center">
                <Col md={10}>
                    <div className="text-center mb-4">
                        <h1>Previsão de Preço de Casas</h1>
                        <p className="lead">
                            Preencha o formulário abaixo para obter uma previsão de preço baseada em um modelo de regressão linear
                        </p>
                    </div>
                    <Row>
                        <Col lg={6}>
                            <div className="mb-4">
                                <PredictionForm />
                            </div>
                        </Col>
                        <Col lg={6}>
                            <PredictionHistory />
                        </Col>
                    </Row>
                </Col>
            </Row>
        </Container>
    );
}

export default App; 