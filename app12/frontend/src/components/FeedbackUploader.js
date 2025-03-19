import React, { useState, useRef } from 'react';
import { Form, Button, Card, Alert, ProgressBar } from 'react-bootstrap';
import axios from 'axios';
import { FaSmile, FaFrown, FaUpload, FaFileUpload } from 'react-icons/fa';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FeedbackUploader = () => {
    const [feedback, setFeedback] = useState('');
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [uploadMode, setUploadMode] = useState('text'); // 'text' ou 'file'
    const fileInputRef = useRef();

    const handleTextChange = (e) => {
        setFeedback(e.target.value);
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            let response;

            if (uploadMode === 'text') {
                if (!feedback.trim()) {
                    throw new Error('Por favor, digite um texto de feedback.');
                }
                response = await axios.post(`${API_URL}/classify-feedback`, { text: feedback });
            } else {
                if (!file) {
                    throw new Error('Por favor, selecione um arquivo para enviar.');
                }

                const formData = new FormData();
                formData.append('file', file);
                response = await axios.post(`${API_URL}/upload-feedback-file`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
            }

            setResult(response.data);
        } catch (err) {
            console.error('Erro ao classificar feedback:', err);
            setError(err.response?.data?.detail || err.message || 'Erro ao classificar o feedback.');
        } finally {
            setLoading(false);
        }
    };

    const formatConfidence = (confidence) => {
        return `${(confidence * 100).toFixed(2)}%`;
    };

    const handleModeChange = (mode) => {
        setUploadMode(mode);
        setFile(null);
        setFeedback('');
        setResult(null);
        setError(null);
    };

    const triggerFileInput = () => {
        fileInputRef.current.click();
    };

    return (
        <Card className="shadow-sm">
            <Card.Body>
                <Card.Title>Envie seu feedback para análise</Card.Title>

                <div className="mb-3">
                    <Button
                        variant={uploadMode === 'text' ? 'primary' : 'outline-primary'}
                        className="me-2"
                        onClick={() => handleModeChange('text')}
                    >
                        Digitar Texto
                    </Button>
                    <Button
                        variant={uploadMode === 'file' ? 'primary' : 'outline-primary'}
                        onClick={() => handleModeChange('file')}
                    >
                        <FaUpload className="me-1" /> Enviar Arquivo
                    </Button>
                </div>

                <Form onSubmit={handleSubmit}>
                    {uploadMode === 'text' ? (
                        <Form.Group className="mb-3">
                            <Form.Label>Texto do feedback</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={5}
                                placeholder="Digite seu feedback aqui..."
                                value={feedback}
                                onChange={handleTextChange}
                                disabled={loading}
                            />
                        </Form.Group>
                    ) : (
                        <div>
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept=".txt,.doc,.docx,.pdf"
                                style={{ display: 'none' }}
                                disabled={loading}
                            />
                            <div
                                className="dropzone"
                                onClick={triggerFileInput}
                                onDragOver={handleDragOver}
                                onDrop={handleDrop}
                            >
                                <FaFileUpload size={30} className="mb-3 text-primary" />
                                <p>Clique ou arraste um arquivo aqui para enviar</p>
                                {file && <p className="text-success">{file.name}</p>}
                            </div>
                            <small className="text-muted">Formatos suportados: TXT</small>
                        </div>
                    )}

                    <Button
                        variant="primary"
                        type="submit"
                        disabled={loading || (uploadMode === 'file' && !file)}
                        className="mt-3"
                    >
                        {loading ? 'Classificando...' : 'Classificar Feedback'}
                    </Button>
                </Form>

                {error && (
                    <Alert variant="danger" className="mt-3">
                        {error}
                    </Alert>
                )}

                {result && (
                    <div className={`feedback-result mt-4 ${result.is_positive ? 'positive' : 'negative'}`}>
                        <div className="d-flex justify-content-between align-items-center mb-3">
                            <h5 className="mb-0">Resultado da Classificação</h5>
                            {result.is_positive ?
                                <FaSmile className="text-success sentiment-icon" /> :
                                <FaFrown className="text-danger sentiment-icon" />
                            }
                        </div>

                        <p><strong>Sentimento:</strong> {result.is_positive ? 'Positivo' : 'Negativo'}</p>
                        <p><strong>Confiança:</strong> {formatConfidence(result.confidence)}</p>

                        <ProgressBar
                            variant={result.is_positive ? "success" : "danger"}
                            now={result.confidence * 100}
                            className="confidence-progress mt-2"
                        />

                        <div className="mt-3">
                            <strong>Texto analisado:</strong>
                            <p className="mt-2">{result.text}</p>
                        </div>
                    </div>
                )}
            </Card.Body>
        </Card>
    );
};

export default FeedbackUploader; 