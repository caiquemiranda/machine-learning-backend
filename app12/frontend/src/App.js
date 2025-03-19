import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import FeedbackUploader from './components/FeedbackUploader';
import FeedbackHistory from './components/FeedbackHistory';

function App() {
    return (
        <Container className="mt-5">
            <Row className="justify-content-center">
                <Col md={11}>
                    <div className="text-center mb-4">
                        <h1>Classificador de Feedbacks</h1>
                        <p className="lead">
                            Envie textos de feedback para classificá-los como positivos ou negativos utilizando machine learning
                        </p>
                    </div>
                    <div className="feedback-container">
                        <Row>
                            <Col lg={6}>
                                <div className="mb-4">
                                    <FeedbackUploader />
                                </div>
                            </Col>
                            <Col lg={6}>
                                <FeedbackHistory />
                            </Col>
                        </Row>
                    </div>
                </Col>
            </Row>
        </Container>
    );
}

export default App; 