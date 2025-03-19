import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import NavigationBar from './components/NavigationBar';
import Dashboard from './components/Dashboard';
import DiagnosticForm from './components/DiagnosticForm';
import ModelTraining from './components/ModelTraining';
import PredictionHistory from './components/PredictionHistory';
import Visualizations from './components/Visualizations';

function App() {
    return (
        <>
            <NavigationBar />
            <Container fluid className="main-container">
                <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/diagnostic" element={<DiagnosticForm />} />
                    <Route path="/training" element={<ModelTraining />} />
                    <Route path="/history" element={<PredictionHistory />} />
                    <Route path="/visualizations" element={<Visualizations />} />
                </Routes>
            </Container>
        </>
    );
}

export default App; 